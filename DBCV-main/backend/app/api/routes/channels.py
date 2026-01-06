import json
import traceback
from typing import Annotated, Any, Union, Optional, List, Tuple
from uuid import UUID
from pydantic import Json
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api.routes.sockets import notify_channel

import app.crud.channel as crud_channel

import app.schemas.channel as schemas_channel
import app.crud.message as crud_message
import app.crud.user as crud_user
import app.crud.bot as crud_bot
from app.models import BotModel, UserModel
from app.models.message import MessageModel
from app.api.dependencies.db import SessionDep
from app.models.channel import ChannelModel, ChannelVariables
from app.schemas.bot import BotSimple, BotSmall
from app.schemas.message import Message, MessagePublic, MessageCreate
from app.api.dependencies.auth import CurrentDeveloper, get_current_user, CurrentUser, CurrentAnyUser
from app.utils.subscribe import subscribe_to_channel, unsubscribe_from_channel
import app.crud.variables as crud_variables
from app.models.role import RoleType
from app.utils.message import publish_message
from app.engine.variables import variable_substitution, replace_variables_universal
from app.utils.users import normalize_user_data
from app.utils.dict import recursive_search_keys
from app.schemas.user import UserCreate
import app.utils.message as message_utils
from app.managers.data_manager import DataManager
from redis.asyncio import Redis
from app.config import settings

from app.database import sessionmanager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=list[schemas_channel.ChannelBuilder],
)
async def read_channels(
        session: SessionDep,
        current_user: CurrentUser,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> list:
    """
    Retrieve channels.
    """
    channels = await ChannelModel.get_all(session, skip, limit, ChannelModel.default_eager_relationships)
    channels = [channel for channel in channels if current_user in channel.subscribers]
    return channels


@router.get(
    "/all",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_channel.ChannelBuilder],
)
async def read_all_channels(
        session: SessionDep,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> list:
    """
    Retrieve channels.
    """
    channels = await ChannelModel.get_all(session, skip, limit, ChannelModel.default_eager_relationships)
    validate_channels = []

    for channel in channels:
        try:

            validate_channels.append(schemas_channel.ChannelBuilder.from_orm(channel))
        except Exception as e:
            ...

    return validate_channels


@router.get(
    "/my",
    response_model=list[schemas_channel.ChannelBuilder],
)
async def read_user_channels(
        session: SessionDep,
        current_user: CurrentUser,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve channels.
    """
    return await ChannelModel.get_all(session, skip, limit, ChannelModel.default_eager_relationships,
                                      owner_id=current_user.id)


@router.get(
    "/{channel_id}",
    response_model=schemas_channel.ChannelBuilder,
)
async def read_channel(
        channel_id: Union[UUID, str],
        session: SessionDep,
        current_user: CurrentAnyUser
) -> Any:
    """
    Get a channel by id.
    """
    channel = await crud_channel.get_channel(session, channel_id)

    if current_user not in channel.subscribers and not channel.is_public:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges.",
        )

    return channel


@router.get(
    "/{channel_id}/messages",
    response_model=list[MessagePublic],
)
async def read_channel_messages(
        session: SessionDep,
        current_user: CurrentAnyUser,
        channel_id: Union[UUID, str],
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,

) -> Any:
    """
    Retrieve channels.
    """
    await message_utils.check_channel_access(session, channel_id, current_user.id)
    channel = await crud_channel.get_channel(session, channel_id, ChannelModel.simple_eager_relationships)
    messages = await MessageModel.get_messages_by_channel(session, channel.id, skip, limit,
                                                          MessageModel.default_eager_relationships)
    return list(reversed(messages))


@router.post(
    "/",
    response_model=schemas_channel.ChannelBuilder,
)
async def create_channel(session: SessionDep, channel_in: schemas_channel.ChannelCreate,
                         current_user: CurrentUser) -> Any:
    """
    Create a channel.
    """
    await crud_channel.check_channel_unique(session, channel_in)
    channel = await crud_channel.create_channel(session, channel_in, current_user)
    await session.commit()
    await session.refresh(channel, attribute_names=["variables", "owner"])
    if channel_in.default_bot_id is not None:
        try:
            await subscribe_to_channel(session, channel.id, channel_in.default_bot_id)
        except Exception:
            logger.exception("Failed to subscribe default bot to channel during creation", extra={
                "channel_id": str(channel.id),
                "default_bot_id": str(channel_in.default_bot_id)
            })
    return channel


@router.post(
    "/{channel_id}/subscribe",
    response_model=Message,
)
async def subscribe(channel_id: Union[UUID, str], session: SessionDep,
                    current_user: CurrentAnyUser, subscribers_ids: List[Union[str, UUID]] = []) -> Any:
    """
    Subscribe to channel
    """

    if subscribers_ids:
        errors = []
        for subscriber_id in subscribers_ids:
            try:
                await subscribe_to_channel(session, channel_id, subscriber_id)
            except Exception as e:
                errors.append(str(e))
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors
            )
        return Message(message="The subscribers has been added to the channel.")
    await subscribe_to_channel(session, channel_id, current_user.id)
    return Message(message="The subscriber has been added to the channel.")


@router.post(
    "/{channel_id}/unsubscribe",
    response_model=Message,
)
async def unsubscribe(channel_id: Union[UUID, str], session: SessionDep,
                      current_user: CurrentAnyUser, subscribers_ids: List[Union[str, UUID]] = []) -> Any:
    """
    Unsubscribe to channel
    """
    if subscribers_ids:
        messages = []
        errors = []
        for subscriber_id in subscribers_ids:
            try:
                await unsubscribe_from_channel(session, channel_id, subscriber_id)
                messages.append(f"The bot with id {subscriber_id} has been unsubscribe from channel")
            except Exception as e:
                errors.append(str(e))
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=messages + errors if messages else errors

            )
        return Message(message="\n".join(messages))
    await unsubscribe_from_channel(session, channel_id, current_user.id)
    return Message(message="The subscriber has been unsubscribe from channel.")


@router.post(
    "/{channel_id}/is_subscriber",
    response_model=schemas_channel.IsSubscriber
)
async def is_subscriber(channel_id: Union[UUID, str],
                        session: SessionDep,
                        current_user: CurrentAnyUser) -> Any:
    """
    Is subscriber to channel
    """
    channel = await crud_channel.get_channel(session, channel_id)
    return schemas_channel.IsSubscriber(is_subscriber=current_user in channel.subscribers)


def prepare_message_data(message: Optional[dict]) -> MessageCreate:
    """
    Prepare message data for creation.
    """
    message_in = MessageCreate(**message)
    if message_in.is_all_none():
        message_in = MessageCreate(params=message)
    return message_in


@router.post(
    "/{channel_id}/message",
    response_model=MessagePublic,
)
async def create_message(session: SessionDep, channel_id: Union[UUID, str], message: Optional[dict]) -> Any:
    """
    Send message to channel.
    """
    channel = await crud_channel.get_channel(session, channel_id)
    message_in = prepare_message_data(message)

    message = await crud_message.create_message(session, message_in, channel_id=channel.id)

    await session.commit()
    await session.refresh(message, attribute_names=["sender", "recipient", "widget", "attachments"])

    # Notify all subscribers in the channel via WebSocket
    await notify_channel(message.channel_id, MessagePublic(**message.__dict__))
    await publish_message(message)
    return message


async def resolve_sender(session: AsyncSession, config: dict | str | None, context: dict) -> tuple[
                                                                                     UserModel | None, Any | None]:
    user_fields = recursive_search_keys(context, {"username", "email"})
    if user_fields:
        try:
            user_data = UserCreate(**normalize_user_data(user_fields))
            user = await crud_user.get_or_create_user(session, user_data)
            message_text = recursive_search_keys(context, {"text"}).get("text")
            return user, message_text
        except Exception as e:
            logger.warning(f"resolve_sender failed: {e}")

    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError:
            config = {}

    resolved = await replace_variables_universal(session, None, config, context)
    normalized = normalize_user_data(resolved)
    user_data = UserCreate(**normalized)

    user = await crud_user.get_or_create_user(session, user_data)
    return user, resolved.get("text")


@router.post(
    "/{channel_id}/{bot_id}/message",
    response_model=MessagePublic,
)
async def create_message(session: SessionDep, channel_id: Union[UUID, str], bot_id: Union[UUID, str],
                         message: Optional[dict]) -> Any:
    """
    Send message to channel.
    """
    channel = await crud_channel.get_channel(session, channel_id)
    bot = await crud_bot.get_bot(session, bot_id, {})
    message_in = prepare_message_data(message)

    if message_in.sender_id is None and bot.config is not None:
        user, message_text = await resolve_sender(session, bot.config, message)
        if user:
            message_in.sender_id = user.id
        if message_text is not None:
            message_in.text = str(message_text)

    message_in.channel_id = channel.id
    message = await message_utils.create_message(session, user, message_in)

    await session.commit()
    await session.refresh(message, attribute_names=["sender", "recipient", "widget", "attachments"])

    # Notify all subscribers in the channel via WebSocket
    await notify_channel(message.channel_id, MessagePublic(**message.__dict__))
    await publish_message(message)
    return message


@router.patch(
    "/{channel_id}",
    response_model=schemas_channel.ChannelBuilder,
)
async def update_channel(
        channel_id: UUID | str, session: SessionDep, channel_in: schemas_channel.ChannelUpdate,
        current_user: CurrentUser
) -> Any:
    """
    Update own channel.
    """
    channel = await crud_channel.get_channel(session, channel_id)
    if not current_user.role == RoleType.ADMIN and channel.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges.",
        )
    await crud_channel.check_channel_unique(session, channel_in, exclude_id=channel_id)
    if channel_in.default_bot_id is not None and channel.default_bot_id != channel_in.default_bot_id:
        await subscribe_to_channel(session, channel_id, channel_in.default_bot_id)

    channel = await crud_channel.update_channel(session, channel_id, channel_in)
    if channel_in.variables:
        variable = await crud_variables.full_update_variable_by_id(session, ChannelVariables, channel.id,
                                                                   channel_in.variables.data)
        await session.commit()
        await session.refresh(variable)
    await session.commit()
    await session.refresh(channel, attribute_names=["variables"])

    redis = Redis.from_url(settings.CACHE_REDIS_URL)
    data_manager = DataManager(redis, sessionmanager.engine)
    await data_manager.update_bot_variables(channel_id, channel_in.variables.data)
    return channel


@router.delete(
    "/{channel_id}",
    response_model=Message)
async def delete_channel(session: SessionDep, channel_id: UUID | str, current_user: CurrentUser) -> Message:
    """
    Delete a channel.
    """
    channel = await crud_channel.get_channel(session, channel_id)
    if not current_user.role == RoleType.ADMIN and channel.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges.",
        )
    await crud_channel.delete_channel(session, channel_id)
    await session.commit()
    return Message(message="Channel deleted successfully.")
