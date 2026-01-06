from typing import Type, Annotated, Any, Optional, Dict
from uuid import UUID

from fastapi import HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.emitter import EmitterModel
from app.models.cron import CronModel
from app.schemas import emitter as schemas_emitter
from app.crud.utils import is_object_unique


async def read_emitters(
    session: AsyncSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    return await EmitterModel.get_all(session, skip, limit)


async def get_emitter(session: AsyncSession, emitter_id: UUID | str,
                      eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[EmitterModel]:
    emitter = await EmitterModel.get_obj(session, emitter_id, eager_relationships)
    if not emitter:
        raise HTTPException(status_code=404, detail="Emitter not found.")
    return emitter


async def create_emitter(
        session: AsyncSession, emitter_in: schemas_emitter.EmitterCreate,
) -> EmitterModel:
    db_obj = EmitterModel(
        **emitter_in.model_dump(),
    )
    session.add(db_obj)
    return db_obj


async def update_emitter(
        session: AsyncSession,
        emitter_id: UUID | str,
        emitter_in: schemas_emitter.EmitterUpdate,
) -> Type[EmitterModel]:
    emitter = await get_emitter(session, emitter_id)
    for key, value in emitter_in.model_dump(exclude_unset=True).items():
        setattr(emitter, key, value)
    return emitter


async def delete_emitter(session: AsyncSession, emitter_id: UUID | str) -> None:
    await session.delete(await get_emitter(session, emitter_id))
