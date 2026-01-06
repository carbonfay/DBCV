from sqlalchemy.ext.asyncio import AsyncSession

import app.crud.message as crud_message
from uuid import UUID

import app.crud.channel as crud_channel
import app.crud.bot as crud_bot

from app.exceptions import ForbiddenException
from app.api.routes.sockets import notify_channel
from app.crud.attachment import create_attachment
from app.schemas.message import MessageCreate, MessagePublic
from app.models.message import MessageModel
from app.models.subscriber import SubscriberModel
from app.crud.channel import get_channel
from app.broker import broker
from app.config import settings

import logging

logger = logging.getLogger(__name__)


async def publish_notify_message(channel_id: UUID | str, message: MessagePublic):
    await broker.publish({"channel_id": str(channel_id), "message": message.dict()}, "message_queue")


async def publish_message(message, stream=settings.USER_STREAM_NAME):
    """
    Publish a message to the broker.
    """
    message_data = {"message": message.get_dict(), "channel_id": None if message.channel_id is None else message.channel_id}
    await broker.publish(message_data, stream=stream)


async def bot_send_message_by_id(session: AsyncSession, message_id: UUID | str, bot_id: UUID | str,
                                 needs_message_processing: bool = True):

    message = await crud_message.get_message(session, message_id)
    if message.channel_id is None:
        logger.warning(f"Message {message_id} has no channel")
        return
    channel = await crud_channel.get_channel(session, message.channel_id)
    bot = await crud_bot.get_bot(session, bot_id, eager_relationships={"channels": {}},)

    if channel.id not in [c.id for c in bot.channels]:
        logger.warning(f"Bot {bot_id} not in channel {channel.id}")
        return
    message_data = message.__dict__
    message_data["sender_id"] = bot_id
    message_clone: MessageModel = await crud_message.create_message(session, MessageCreate(**message_data),
                                                                    channel_id=message.channel_id)

    await session.commit()
    await session.refresh(message_clone, attribute_names=["sender", "recipient", "widget", "attachments"])
    await notify_channel(message_clone.channel_id, MessagePublic(**message_clone.__dict__))
    if needs_message_processing:
        await publish_message(message_clone, stream=settings.BOT_STREAM_NAME)


async def check_channel_access(session: AsyncSession, channel_id: UUID, subscriber_id: UUID):
    """
    Check if the subscriber has access to the specified channel.
    """
    channel = await crud_channel.get_channel(session, channel_id)

    if subscriber_id in {sub.id for sub in channel.subscribers}:
        return channel

    if channel.is_public:
        from app.utils.subscribe import subscribe_to_channel
        await subscribe_to_channel(session, channel_id, subscriber_id)
        return channel

    raise ForbiddenException


async def attach_files(session: AsyncSession, attachments: list, message: MessageModel):
    """
    Create and attach files to the message.
    """
    if attachments:
        created_attachments = [await create_attachment(session, attachment) for attachment in attachments]
        message.attachments = created_attachments


async def create_message(session: AsyncSession, current_user: SubscriberModel, message_in: MessageCreate, attachments: list = []):
    """
    Create a message and handle attachments.
    """
    channel = None
    if message_in.channel_id:
        channel = await check_channel_access(session, message_in.channel_id, current_user.id)

    message = await crud_message.create_message(session, message_in, channel_id=None if channel is None else channel.id)
    await attach_files(session, attachments, message)

    await session.commit()
    await session.refresh(message, attribute_names=["sender", "recipient", "widget", "attachments"])
    return message
