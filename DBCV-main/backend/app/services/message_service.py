from sqlalchemy.ext.asyncio import AsyncEngine  
from app.engine.variables import variable_substitution_pydantic
from app.managers.message_manager import MessageManager
from app.managers.widget_manager import WidgetManager
from app.schemas.message import MessagePublic, MessageCreate
from app.schemas.session import SessionSimple
from app.utils.message import publish_notify_message, check_channel_access
from app.utils.widget import prepare_widget_copy_data



class MessageService:
    def __init__(self, engine: AsyncEngine):
        self.message_manager = MessageManager(engine)
        self.widget_manager = WidgetManager(engine)

    async def send_message(self, session: SessionSimple, message_schema: MessagePublic, context: dict) -> dict:

        # TODO: Реализовать проверку доступа
        # recipient_id = message_schema.recipient_id or session.user_id
        # await check_channel_access(...)

        message_copy_in: MessagePublic = await variable_substitution_pydantic(message_schema, context)

        if message_copy_in.widget:
            widget_data = message_copy_in.widget.model_dump()
            widget_copy_data = prepare_widget_copy_data(widget_data)
            new_widget = await self.widget_manager.insert(widget_copy_data)
            message_copy_in.widget_id = new_widget["id"]
            message_copy_in.widget = new_widget

        message_copy_in.sender_id = str(session.bot_id)
        message_copy_in.recipient_id = str(session.user_id)
        message_copy_in.channel_id = str(session.channel_id)

        msg_data = MessageCreate(**message_copy_in.model_dump()).model_dump()

        new_message = await self.message_manager.insert(msg_data)
        new_message["widget"] = message_copy_in.widget
        new_message_in = MessagePublic(**new_message)
        await publish_notify_message(session.channel_id, new_message_in)
        return new_message