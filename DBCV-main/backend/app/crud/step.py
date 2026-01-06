from typing import Type, List, Sequence, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models import StepModel
from app.models.step import StepModel
from app.schemas import step as schemas_step
from app.crud.utils import is_object_unique
from app.crud.message import create_message
from app.crud.bot import get_bot


async def check_step_unique(
        session: AsyncSession,
        step_in: schemas_step.StepBase,
        exclude_id: UUID | str | None = None,
) -> None:
    if not await is_step_unique(session, step_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The step with the given name already exists.",
        )


async def is_step_unique(
        session: AsyncSession,
        step_in: schemas_step.StepBase | schemas_step.StepUpdate,
        exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        StepModel,
        step_in,
        unique_fields=("name",),
        exclude_id=exclude_id,
    )


async def get_step(session: AsyncSession, step_id: UUID | str,
                   eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[StepModel]:
    step = await StepModel.get_obj(session, step_id, eager_relationships)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found.")
    return step


async def create_step(
        session: AsyncSession, step_in: schemas_step.StepCreate,
) -> StepModel:
    db_obj = StepModel(
        **step_in.model_dump(),
    )
    session.add(db_obj)
    return db_obj


async def update_step(
        session: AsyncSession,
        step_id: UUID | str,
        step_in: schemas_step.StepUpdate,
) -> Type[StepModel]:
    step = await get_step(session, step_id)
    for key, value in step_in.model_dump(exclude_unset=True).items():
        setattr(step, key, value)
    return step


async def delete_step(session: AsyncSession, step_id: UUID | str) -> None:
    await session.delete(await get_step(session, step_id))


async def get_steps_by_bot(session: AsyncSession, bot_id: UUID | str) -> Sequence[StepModel]:
    return (
        await session.scalars(select(StepModel).where(getattr(StepModel, "bot_id") == bot_id))
    ).fetchall()

