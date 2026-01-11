from typing import Annotated, Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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


class RunStepRequest(BaseModel):
    variables: Optional[dict] = None
    context: Optional[dict] = None
    bot_id: Optional[str] = None


@router.post("/{step_id}/run")
async def run_step(
    step_id: Union[UUID, str],
    request: RunStepRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Execute a step (used by builder UI). Runs connection groups sequentially and returns
    results for each group plus final variables.
    """
    # Access check
    await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)

    # Load step with relationships
    step = await crud_step.get_step(session, step_id, StepModel.default_eager_relationships)
    from app.schemas.step import StepExport
    step_export = StepExport.model_validate(step)

    # Prepare runtime helpers
    from types import SimpleNamespace
    from app.engine.bot_processor import ConnectionHandlerFactory, redis as engine_redis
    from app.auth.credentials_resolver import CredentialsResolver
    from app.auth.service import AuthService
    from app.managers.data_manager import DataManager
    from app.loggers.bot import BotLogger
    from app.engine.variables import update_variables_dict
    from app.database import sessionmanager

    bot_id = request.bot_id or step_export.bot_id
    bot_obj = SimpleNamespace(id=bot_id)

    data_manager = DataManager(engine_redis, sessionmanager.engine)
    logger = BotLogger(bot_id)

    all_variables = request.variables or {}
    context = request.context or {}

    results: list[dict] = []

    for group in step_export.connection_groups:
        group_result = {
            "group_id": str(group.id),
            "search_type": getattr(group.search_type, 'value', str(group.search_type)),
            "priority": getattr(group, 'priority', 0),
            "result": None,
            "variables_updated": None,
        }

        try:
            resolver = CredentialsResolver(data_manager)
            auth_service = AuthService(resolver)
            handler = ConnectionHandlerFactory.get_handler(group.search_type, logger, bot=bot_obj, auth=auth_service, data_manager=data_manager)
            if not handler:
                group_result["result"] = None
                results.append(group_result)
                continue

            result = await handler.handle(group, context, all_variables)
            group_result["result"] = result

            # Try to update variables in memory using group's variables mapping (does not persist)
            try:
                if getattr(group, 'variables', None):
                    updated = await update_variables_dict(all_variables, session, group.variables or {}, context or {})
                    all_variables = updated
                    group_result["variables_updated"] = updated
                else:
                    group_result["variables_updated"] = None
            except Exception as e:
                await logger.error(f"Error updating variables for group {group.id}: {e}")
                group_result["variables_updated"] = None

        except Exception as e:
            import traceback
            tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            group_result["result"] = {"error": str(e), "traceback": tb}

        results.append(group_result)

    return JSONResponse({"results": results, "final_variables": all_variables})


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



