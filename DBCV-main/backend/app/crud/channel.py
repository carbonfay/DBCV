from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import MessageModel
from app.models.widget import WidgetModel
from app.api.dependencies.auth import CurrentUser
from app.models.channel import ChannelModel
from app.schemas import channel as schemas_channel
from app.crud.utils import is_object_unique
from app.crud.user import get_user


async def check_channel_unique(
    session: AsyncSession,
    channel_in: schemas_channel.ChannelBase,
    exclude_id: UUID | str | None = None,
) -> None:
    if not await is_channel_unique(session, channel_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The channel with the given name already exists.",
        )


async def is_channel_unique(
    session: AsyncSession,
    channel_in: schemas_channel.ChannelBase | schemas_channel.ChannelUpdate,
    exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        ChannelModel,
        channel_in,
        unique_fields=("name", ),
        exclude_id=exclude_id,
    )


async def get_channel(session: AsyncSession, channel_id: UUID | str,
                      eager_relationships: Optional[Dict[str, Any]] = None) -> Type[ChannelModel]:
    channel = await ChannelModel.get_obj(session, channel_id, eager_relationships)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    return channel


async def create_channel(
    session: AsyncSession, channel_in: schemas_channel.ChannelCreate, owner: CurrentUser | None = None
) -> ChannelModel:
    if owner is None:
        owner = await get_user(session, channel_in.owner_id)
    db_obj = ChannelModel(
        **channel_in.model_dump(exclude={"owner_id"}),
        owner=owner,
        subscribers=[owner]
    )
    session.add(db_obj)
    return db_obj


async def update_channel(
    session: AsyncSession,
    channel_id: UUID | str,
    channel_in: schemas_channel.ChannelUpdate,
) -> Type[ChannelModel]:
    channel = await get_channel(session, channel_id)
    for key, value in channel_in.model_dump(exclude_unset=True, exclude={"variables"}).items():
        setattr(channel, key, value)
    return channel


async def delete_channel(session: AsyncSession, channel_id: UUID | str) -> None:
    messages_to_delete = await session.execute(
        select(MessageModel).where(
            MessageModel.channel_id == channel_id,
            MessageModel.step_id.is_(None)
        )
    )
    
    messages_list = list(messages_to_delete.scalars())

    await session.execute(
        MessageModel.__table__.update().where(
            MessageModel.channel_id == channel_id,
            MessageModel.step_id.is_(None)
        ).values(widget_id=None)
    )
    
    result = await session.execute(
        delete(MessageModel).where(
            MessageModel.channel_id == channel_id,
            MessageModel.step_id.is_(None)
        )
    )
    
    widget_ids_to_delete = set()
    for message in messages_list:
        if message.widget_id:
            widget_ids_to_delete.add(message.widget_id)
    
    if widget_ids_to_delete:
        result = await session.execute(
            delete(WidgetModel).where(WidgetModel.id.in_(widget_ids_to_delete))
        )
    
    await session.delete(await get_channel(session, channel_id))
