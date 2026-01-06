from typing import Annotated, Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from fastapi.responses import JSONResponse

import app.crud.cron as crud_cron
import app.crud.bot as crud_bot
import app.crud.channel as crud_channel
import app.schemas.cron as schemas_cron
from app.api.dependencies.db import SessionDep
from app.models.cron import CronModel
from app.schemas.message import Message
from app.api.dependencies.auth import CurrentUser, CurrentDeveloper
router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_cron.CronPublic],
)
async def read_crons(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve crons.
    """
    statement = select(CronModel).offset(skip)
    if limit:
        statement = statement.limit(limit)
    return list((await session.scalars(statement)).all())


@router.post(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=schemas_cron.CronPublic,
)
async def create_cron(session: SessionDep, cron_in: schemas_cron.CronCreate) -> Any:
    """
    Create a cron.
    """
    cron = await crud_cron.create_cron(session, cron_in)
    await session.commit()
    await session.refresh(cron)
    return cron


@router.patch(
    "/{cron_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_cron.CronPublic,
)
async def update_cron(
    cron_id: Union[UUID, str], session: SessionDep, cron_in: schemas_cron.CronUpdate
) -> Any:
    """
    Update a cron.
    """
    cron = await crud_cron.update_cron(session, cron_id, cron_in)
    await session.commit()
    await session.refresh(cron)
    return cron


@router.delete("/{cron_id}",
               dependencies=[CurrentDeveloper],
               response_model=Message)
async def delete_cron(session: SessionDep, cron_id: Union[UUID, str]) -> Message:
    """
    Delete a cron.
    """
    await crud_cron.delete_cron(session, cron_id)
    await session.commit()
    return Message(message="Cron deleted successfully.")