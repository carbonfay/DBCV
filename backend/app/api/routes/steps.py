from typing import Annotated, Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from fastapi.responses import JSONResponse

import app.crud.step as crud_step
import app.crud.bot as crud_bot
import app.crud.channel as crud_channel
import app.crud.message as crud_message
import app.schemas.step as schemas_step
from app.api.dependencies.db import SessionDep
from app.api.routes.sockets import notify_channel
from app.models.step import StepModel
from app.models.access import AccessType
from app.schemas.message import Message, MessageCreate, MessagePublic
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentAdmin
from app.api.dependencies.auth import BotAccessChecker
router = APIRouter()


@router.get(
    "/",
    response_model=list[schemas_step.StepPublic],
    dependencies=[CurrentAdmin]
)
async def read_steps(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve steps.
    """
    return await StepModel.get_all(session, skip, limit)


@router.post(
    "/",
    response_model=schemas_step.StepSimple,
)
async def create_step(session: SessionDep, current_user: CurrentUser, step_in: schemas_step.StepCreate) -> Any:
    """
    Create a step.
    """
    await BotAccessChecker._has_access(session, step_in.bot_id, current_user, AccessType.EDITOR)
    step = await crud_step.create_step(session, step_in)
    await session.commit()
    await session.refresh(step)
    return step


@router.patch(
    "/{step_id}",
    response_model=schemas_step.StepPublic,
)
async def update_step(
    step_id: Union[UUID, str], session: SessionDep,  current_user: CurrentUser, step_in: schemas_step.StepUpdate,
) -> Any:
    """
    Update a step.
    """
    await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)
    step = await crud_step.update_step(session, step_id, step_in)
    await session.commit()
    await session.refresh(step)
    return step


@router.delete("/{step_id}",
               response_model=Message)
async def delete_step(session: SessionDep, current_user: CurrentUser, step_id: Union[UUID, str]) -> Message:
    """
    Delete a step.
    """
    await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)
    await crud_step.delete_step(session, step_id)
    await session.commit()
    return Message(message="Step deleted successfully.")



