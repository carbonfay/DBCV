from typing import Type, Annotated, Any, Optional, Dict
from uuid import UUID

from fastapi import HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.cron import CronModel
from app.schemas import cron as schemas_cron
from app.crud.utils import is_object_unique


async def get_cron(session: AsyncSession, cron_id: UUID | str,
                   eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[CronModel]:
    cron = await CronModel.get_obj(session, cron_id, eager_relationships)
    if not cron:
        raise HTTPException(status_code=404, detail="Cron not found.")
    return cron


async def create_cron(
        session: AsyncSession, cron_in: schemas_cron.CronCreate,
) -> CronModel:
    db_obj = CronModel(
        **cron_in.model_dump(),
    )
    session.add(db_obj)
    return db_obj


async def update_cron(
        session: AsyncSession,
        cron_id: UUID | str,
        cron_in: schemas_cron.CronUpdate,
) -> Type[CronModel]:
    cron = await get_cron(session, cron_id)
    for key, value in cron_in.model_dump(exclude_unset=True, exclude={"id"}).items():
        setattr(cron, key, value)
    return cron


async def delete_cron(session: AsyncSession, cron_id: UUID | str) -> None:
    await session.delete(await get_cron(session, cron_id))
