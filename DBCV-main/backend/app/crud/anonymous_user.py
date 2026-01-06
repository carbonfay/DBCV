from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anonymous_user import AnonymousUserModel


async def get_anonymous_user(session: AsyncSession, anonymous_user_id: UUID | str,
                             eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[AnonymousUserModel]:
    anonymous_user = await AnonymousUserModel.get_obj(session, anonymous_user_id, eager_relationships)
    if not anonymous_user:
        raise HTTPException(status_code=404, detail="Anonymous user not found.")
    return anonymous_user


async def create_anonymous_user(
    session: AsyncSession,
) -> AnonymousUserModel:
    db_obj = AnonymousUserModel()
    session.add(db_obj)
    return db_obj


async def delete_anonymous_user(session: AsyncSession, anonymous_user_id: UUID | str) -> None:
    await session.delete(await get_anonymous_user(session, anonymous_user_id))
