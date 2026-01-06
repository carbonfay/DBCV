from typing import Annotated, Any, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

import app.crud.emitter as crud_emitter
import app.crud.cron as crud_cron
import app.crud.user as crud_user
import app.schemas.emitter as schemas_emitter
from app.api.dependencies.db import SessionDep
from app.models.emitter import EmitterModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, BotAccessChecker
from app.models.access import AccessType
from uuid import UUID
from app.scheduler import scheduler, publish_emitter_event
router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_emitter.EmitterPublic],
)
async def read_emitters(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve emitters.
    """
    return await crud_emitter.read_emitters(session, skip, limit)


@router.get("/{emitter_id}",
            dependencies=[CurrentDeveloper],
            response_model=schemas_emitter.EmitterPublic)
async def read_emitter(
    emitter_id: Union[UUID, str], session: SessionDep,
) -> Any:
    """
    Get a specific emitter by id.
    """
    emitter = await crud_emitter.get_emitter(session, emitter_id)
    return emitter


@router.post(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=schemas_emitter.EmitterPublic,
)
async def create_emitter(session: SessionDep, emitter_in: schemas_emitter.EmitterCreate, current_user: CurrentUser) -> Any:
    """
    Create a emitter.
    """
    await BotAccessChecker._has_access(session, emitter_in.bot_id, current_user, AccessType.EDITOR)
    emitter = await crud_emitter.create_emitter(session, emitter_in)
    await session.commit()
    await session.refresh(emitter)
    await publish_emitter_event("emitter.created",
                                schemas_emitter.EmitterPublic.model_validate(emitter).model_dump())
    return emitter


@router.patch(
    "/{emitter_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_emitter.EmitterPublic,
)
async def update_emitter(
    emitter_id: Union[UUID, str], session: SessionDep, emitter_in: schemas_emitter.EmitterUpdate, current_user: CurrentUser
) -> Any:
    """
    Update a emitter.
    """
    await BotAccessChecker._has_access_by_emitter(session, emitter_id, current_user, AccessType.EDITOR)
    emitter = await crud_emitter.update_emitter(session, emitter_id, emitter_in)
    await session.commit()
    await session.refresh(emitter)
    await publish_emitter_event("emitter.updated",
                                schemas_emitter.EmitterPublic.model_validate(emitter).model_dump())
    return emitter


@router.delete("/{emitter_id}",
               dependencies=[CurrentDeveloper])
async def delete_emitter(session: SessionDep, emitter_id: Union[UUID, str], current_user: CurrentUser) -> Message:
    """
    Delete a emitter.
    """
    await BotAccessChecker._has_access_by_emitter(session, emitter_id, current_user, AccessType.EDITOR)
    emitter = await crud_emitter.get_emitter(session, emitter_id)
    await publish_emitter_event("emitter.deleted",
                                schemas_emitter.EmitterPublic.model_validate(emitter).model_dump())
    return Message(message="Emitter deleted successfully.")

