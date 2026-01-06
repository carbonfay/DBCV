from typing import Type, Union, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import with_polymorphic
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.subscriber import SubscriberModel
from app.models.user import UserModel
from app.models.bot import BotModel
from sqlalchemy import select
from app.schemas import subscriber as schemas_subscriber
from app.crud.utils import is_object_unique


async def get_subscriber(session: AsyncSession, subscriber_id: UUID | str,
                         eager_relationships: Optional[Dict[str, Any]] = None,) -> Union[UserModel, BotModel]:
    subscriber = await SubscriberModel.get_obj(session, subscriber_id, eager_relationships)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found.")
    return subscriber


async def delete_subscriber(session: AsyncSession, subscriber_id: UUID | str) -> None:
    await session.delete(await get_subscriber(session, subscriber_id))
