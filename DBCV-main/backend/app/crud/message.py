from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.message import MessageModel
from app.schemas import message as schemas_message
from app.crud.utils import is_object_unique


async def get_message(session: AsyncSession, message_id: UUID | str,
                      eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[MessageModel]:
    message = await MessageModel.get_obj(session, message_id, eager_relationships)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found.")
    return message


async def create_message(
    session: AsyncSession, message_in: schemas_message.MessageCreate | schemas_message.MessagePrivateCreate, channel_id: UUID | str | None,
) -> MessageModel:
    db_obj = MessageModel(
        **message_in.model_dump(exclude={"channel_id"}),
        channel_id=channel_id,
    )
    session.add(db_obj)
    return db_obj


async def update_message(
    session: AsyncSession,
    message_id: UUID | str,
    message_in: schemas_message.MessageUpdate | schemas_message.MessagePrivateUpdate,
) -> Type[MessageModel]:
    message = await get_message(session, message_id)
    for key, value in message_in.model_dump(exclude_unset=True).items():
        setattr(message, key, value)
    return message


async def delete_message(session: AsyncSession, message_id: UUID | str) -> None:
    await session.delete(await get_message(session, message_id))


async def prepare_message_copy(message_copy_in: schemas_message.MessageCreate,
                               sender_id: UUID | str | None,
                               recipient_id: UUID | str | None) -> schemas_message.MessageCreate:
    """
    Prepare a message copy with updated sender and recipient IDs.
    """
    message_copy_in.recipient_id = recipient_id
    message_copy_in.sender_id = sender_id
    return message_copy_in


async def create_copy_message(session: AsyncSession, message_copy_in: schemas_message.MessageCreate,
                              sender_id: UUID | str | None = None, recipient_id: UUID | str | None = None, channel_id: UUID | str | None = None):
    """
    Create a copy of a message.
    """
    message_copy_in = await prepare_message_copy(message_copy_in, sender_id, recipient_id)
    new_message = await create_message(session, message_copy_in, channel_id)
    await session.commit()
    await session.refresh(new_message)
    return new_message
