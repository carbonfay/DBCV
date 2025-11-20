import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from app.api.routes.sockets import notify_channel
from app.config import settings
from app.engine.variables import variable_substitution_pydantic
from app.models import SessionModel, MessageModel
from app.schemas.message import MessageCreate, MessagePublic, MessageSubstitute
from app.schemas.session import SessionSimple
from app.schemas.widget import WidgetCreate
import app.crud.message as crud_message
import app.crud.widget as crud_widget
import logging
from app.utils.message import publish_notify_message, publish_message, check_channel_access
from app.utils.widget import create_widget_copy as utils_create_widget_copy
logger = logging.getLogger(__name__)


async def create_copy_message(session: AsyncSession, message_copy_in: MessagePublic,
                              sender_id: UUID | str | None = None,
                              recipient_id: UUID | str | None = None,
                              channel_id: UUID | str | None = None):
    """
    Create a copy of a message, including its widget if applicable.
    """
    new_widget = None
    if message_copy_in.widget_id:
        new_widget = await utils_create_widget_copy(session, message_copy_in.widget.model_dump())

    message_copy_in.recipient_id = recipient_id
    message_copy_in.sender_id = sender_id
    message_copy_in.widget_id = new_widget.id if new_widget else None

    new_message = await crud_message.create_message(session, MessageCreate(**message_copy_in.model_dump()), channel_id)
    await session.commit()
    await session.refresh(new_message, attribute_names=["sender", "recipient", "widget", "attachments"])
    return new_message


async def send_copy_message(session: AsyncSession,
                            session_obj: SessionModel,
                            message_copy: MessageModel | None,
                            context: dict | None = None):
    if message_copy is not None:

        message_copy_in: MessageSubstitute = MessageSubstitute.model_validate(message_copy)

        message_copy_in = await variable_substitution_pydantic(message_copy_in, context)
        recipient_id = session_obj.user_id
        if message_copy_in.recipient_id:
            await check_channel_access(session, session_obj.channel_id, message_copy_in.recipient_id)
            recipient_id = message_copy_in.recipient_id

        new_message = await create_copy_message(session, message_copy_in,
                                                sender_id=session_obj.bot_id,
                                                recipient_id=recipient_id,
                                                channel_id=session_obj.channel_id)

        await publish_notify_message(new_message.channel_id, MessagePublic.model_validate(new_message))
        await publish_message(new_message, stream=settings.BOT_STREAM_NAME)
        return new_message
    return None