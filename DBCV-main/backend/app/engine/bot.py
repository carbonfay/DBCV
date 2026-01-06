from typing import Type
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status
from app.crud.session import create_session, get_session
from app.schemas.session import SessionCreate
from app.models.channel import ChannelModel
from app.models.message import MessageModel
from app.crud.bot import get_bot
from app.crud.subscriber import get_subscriber
from app.engine.message import send_copy_message


async def start_work_in_channel(session: AsyncSession, channel: Type[ChannelModel], bot_id: UUID | str) -> None:
    bot = await get_bot(session, bot_id)
    if bot.first_step is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The bot doesn't have first step.",
        )

    for subscriber in channel.subscribers:
        if subscriber.id == bot.id:
            continue
            
        session_obj = await get_session(session, user_id=subscriber.id, bot_id=bot.id,
                                        channel_id=channel.id)
        if session_obj is None:
            session_obj = await create_session(session, SessionCreate(user_id=subscriber.id, bot_id=bot.id,
                                                                      channel_id=channel.id, step_id=bot.first_step.id))
        else:
            session_obj.step_id = bot.first_step.id
        await session.commit()
        await session.refresh(session_obj)

        message: MessageModel | None = bot.first_step.message
        
        await session.refresh(bot, ["variables"])
        await session.refresh(subscriber, ["variables"])
        await session.refresh(channel, ["variables"])
        await session.refresh(session_obj, ["variables"])
        
        context = {
            "bot": bot.variables.get_data() if bot.variables else {},
            "user": subscriber.variables.get_data() if hasattr(subscriber, 'variables') and subscriber.variables else {},
            "channel": channel.variables.get_data() if channel.variables else {},
            "session": session_obj.variables.get_data() if session_obj.variables else {}
        }
        await send_copy_message(session, session_obj, message, context)


async def start_work_for_subscriber(session: AsyncSession, channel: Type[ChannelModel], user_id: UUID | str) -> None:
    user = await get_subscriber(session, user_id)
    for subscriber in channel.subscribers:
        if subscriber.is_bot():
            bot = subscriber
            await session.refresh(bot, ["first_step"])
            if bot.first_step:
                session_obj = await get_session(session, user_id=user.id, bot_id=bot.id, channel_id=channel.id)
                if session_obj is None:
                    session_obj = await create_session(session, SessionCreate(user_id=user.id, bot_id=bot.id,
                                                                              channel_id=channel.id,
                                                                              step_id=bot.first_step.id))
                await session.commit()
                await session.refresh(session_obj)

                message: MessageModel | None = bot.first_step.message
                
                await session.refresh(bot, ["variables"])
                await session.refresh(user, ["variables"])
                await session.refresh(channel, ["variables"])
                await session.refresh(session_obj, ["variables"])
                
                context = {
                    "bot": bot.variables.get_data() if bot.variables else {},
                    "user": user.variables.get_data() if user.variables else {},
                    "channel": channel.variables.get_data() if channel.variables else {},
                    "session": session_obj.variables.get_data() if session_obj.variables else {}
                }
                await send_copy_message(session, session_obj, message, context)
