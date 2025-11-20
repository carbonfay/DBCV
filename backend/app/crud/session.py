from typing import Type, Optional, Dict, Any, List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models import SessionModel
from app.models.session import SessionModel
from app.schemas import session as schemas_session
from app.crud.utils import is_object_unique


async def check_session_unique(
        session: AsyncSession,
        session_in: schemas_session.SessionBase,
        exclude_id: UUID | str | None = None,
) -> None:
    if not await is_session_unique(session, session_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The user with the given email or username already exists.",
        )


async def is_session_unique(
        session: AsyncSession,
        user_in: schemas_session.SessionBase,
        exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        SessionModel,
        user_in,
        unique_fields=("user_id", "bot_id", "channel_id"),
        exclude_id=exclude_id,
    )


async def get_sessions(session: AsyncSession,
                       user_id: Optional[UUID | str] = None,
                       bot_id: Optional[UUID | str] = None,
                       channel_id: Optional[UUID | str] = None
                       ) -> (List[SessionModel] | None):
    whereclause = []
    if user_id:
        whereclause.append(SessionModel.user_id == user_id)
    if bot_id:
        whereclause.append(SessionModel.bot_id == bot_id)
    if channel_id:
        whereclause.append(SessionModel.channel_id == channel_id)
    return list((
                    await session.scalars(select(SessionModel).where(*whereclause))
                ).all())


async def get_sessions_by_user(session: AsyncSession, user_id: UUID | str) -> (
        List[SessionModel] | None):
    return await get_sessions(session, user_id=user_id)


async def get_sessions_by_bot(session: AsyncSession, bot_id: UUID | str) -> (
        List[SessionModel] | None):
    return await get_sessions(session, bot_id=bot_id)


async def get_sessions_by_channel(session: AsyncSession, channel_id: UUID | str) -> (
        List[SessionModel] | None):
    return await get_sessions(session, channel_id=channel_id)


async def get_session(session: AsyncSession, user_id: UUID | str, bot_id: UUID | str, channel_id: UUID | str) -> (
        SessionModel | None):
    return (
        await session.scalars(select(SessionModel).where(SessionModel.user_id == user_id,
                                                         SessionModel.bot_id == bot_id,
                                                         SessionModel.channel_id == channel_id,
                                                         )
                              )
    ).one_or_none()


async def get_session_by_id(session: AsyncSession, session_id,
                            eager_relationships: Optional[Dict[str, Any]] = None, ) -> Type[SessionModel]:
    session = await SessionModel.get_obj(session, session_id, eager_relationships)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


async def create_session(
        session: AsyncSession, session_in: schemas_session.SessionCreate,
) -> SessionModel:
    db_obj = SessionModel(
        **session_in.model_dump(),
    )
    session.add(db_obj)
    return db_obj


async def update_session(
        session: AsyncSession,
        session_id: UUID,
        session_in: schemas_session.SessionUpdate,
) -> Type[SessionModel]:
    session = await get_session_by_id(session, session_id)
    for key, value in session_in.model_dump(exclude_unset=True).items():
        setattr(session, key, value)
    return session


async def delete_session(session: AsyncSession, user_id: UUID | str, bot_id: UUID | str,
                         channel_id: UUID | str) -> None:
    await session.delete(await get_session(session, user_id, bot_id, channel_id))


async def delete_session_by_id(session: AsyncSession, session_id) -> None:
    await session.delete(await get_session_by_id(session, session_id))
