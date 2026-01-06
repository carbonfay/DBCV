import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import app.crud.subscriber as crud_subscriber
import app.crud.channel as crud_channel
import app.engine.bot as bot_engine
import app.crud.session as crud_session
from app.managers.data_manager import DataManager
from redis.asyncio import Redis
from app.config import settings
from app.database import sessionmanager


async def update_subscribers_cache(channel):
    subscribers_ids = [{"id": sub.id} for sub in channel.subscribers if sub.is_bot()]
    data_manager = DataManager(Redis.from_url(settings.CACHE_REDIS_URL), sessionmanager.engine)
    await data_manager.update_channel_subscribers(channel.id, subscribers_ids)


async def subscribe_to_channel(session: AsyncSession, channel_id: UUID | str, subscriber_id: UUID | str):
    subscriber = await crud_subscriber.get_subscriber(session, subscriber_id)
    channel = await crud_channel.get_channel(session, channel_id)
    if subscriber not in channel.subscribers:
        channel.subscribers.append(subscriber)

        await update_subscribers_cache( channel)

        if subscriber.is_bot():
            await bot_engine.start_work_in_channel(session, channel, subscriber.id)
        if subscriber.is_any_user():
            await bot_engine.start_work_for_subscriber(session, channel, subscriber.id)

        await session.commit()


async def unsubscribe_from_channel(session: AsyncSession, channel_id: UUID | str, subscriber_id: UUID | str):
    subscriber = await crud_subscriber.get_subscriber(session, subscriber_id)
    channel = await crud_channel.get_channel(session, channel_id)
    if subscriber in channel.subscribers:
        channel.subscribers.remove(subscriber)

        await update_subscribers_cache(channel)

        sessions = await crud_session.get_sessions(session, channel_id=channel_id, user_id=subscriber_id)
        for session_obj in sessions:
            await session.delete(session_obj)
        await session.commit()
        await session.refresh(channel)
