from typing import Annotated, Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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
from app.models.connection import SearchType
from app.auth.credentials_resolver import CredentialsResolver
from app.auth.inline_credentials_resolver import InlineCredential, InlineCredentialsResolver
from app.database import sessionmanager
from app.loggers.collecting import CollectingBotLogger
from app.managers.data_manager import DataManager
from app.schemas.connection import ConnectionGroupExport
from app.services.step_runner import run_integration_connection_group, StepRunError

try:
    import app.integrations  # noqa: F401
except ImportError:  # pragma: no cover
    pass

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


class StepRunCredential(BaseModel):
    provider: str
    strategy: Optional[str] = None
    payload: dict = Field(default_factory=dict)


class StepRunRequest(BaseModel):
    context: dict = Field(default_factory=dict, description="Runtime input/context (e.g. from UI)")
    all_variables: dict = Field(default_factory=dict, description="Variables available for substitutions")
    connection_group_id: Optional[Union[UUID, str]] = Field(
        default=None,
        description="If set, execute only this connection group (must belong to the step)",
    )
    credentials: list[StepRunCredential] = Field(
        default_factory=list,
        description="Optional inline credentials (skips DB/Redis lookup)",
    )


class StepRunGroupResult(BaseModel):
    connection_group_id: Union[UUID, str]
    search_type: SearchType
    output: dict


class StepRunResponse(BaseModel):
    step_id: Union[UUID, str]
    results: list[StepRunGroupResult]
    all_variables: dict
    logs: list[dict] = Field(default_factory=list)


@router.post(
    "/{step_id}/run",
    response_model=StepRunResponse,
    summary="Run a step's integration blocks",
    description="Executes integration-type connection groups for a step (optionally a single group) and returns outputs + updated variables.",
)
async def run_step(
    step_id: Union[UUID, str],
    session: SessionDep,
    current_user: CurrentUser,
    payload: StepRunRequest,
) -> Any:
    await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)

    step = await crud_step.get_step(session, step_id)
    if not step.bot_id:
        raise HTTPException(status_code=400, detail="Step has no bot_id")

    logger = CollectingBotLogger(bot_id=str(step.bot_id))
    logger.set_step(str(step_id))

    if payload.credentials:
        resolver = InlineCredentialsResolver(
            [
                InlineCredential(provider=c.provider, strategy=c.strategy, payload=c.payload)
                for c in payload.credentials
            ]
        )
    else:
        from redis.asyncio import Redis
        from app.config import settings

        dm = DataManager(Redis.from_url(settings.CACHE_REDIS_URL), sessionmanager.engine)
        resolver = CredentialsResolver(dm)

    connection_groups = list(step.connection_groups or [])
    if payload.connection_group_id is not None:
        connection_groups = [cg for cg in connection_groups if str(cg.id) == str(payload.connection_group_id)]
        if not connection_groups:
            raise HTTPException(status_code=404, detail="connection_group not found for the step")

    # For now, "run" endpoint focuses on integrations (blocks in UI).
    connection_groups = [cg for cg in connection_groups if cg.search_type == SearchType.integration]
    if not connection_groups:
        raise HTTPException(status_code=400, detail="No integration connection groups to run")

    all_variables = payload.all_variables or {}
    context = payload.context or {}

    results: list[StepRunGroupResult] = []
    try:
        for cg in connection_groups:
            cg_export = ConnectionGroupExport.model_validate(cg)
            output, all_variables = await run_integration_connection_group(
                db_session=session,
                connection_group=cg_export,
                context=context,
                all_variables=all_variables,
                bot_id=step.bot_id,
                credentials_resolver=resolver,
                logger=logger,
            )
            results.append(
                StepRunGroupResult(
                    connection_group_id=cg_export.id,
                    search_type=cg_export.search_type,
                    output=output,
                )
            )
    except StepRunError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        await logger.error(f"Step run failed: {exc}")
        raise HTTPException(status_code=500, detail="Step run failed")

    return StepRunResponse(
        step_id=step_id,
        results=results,
        all_variables=all_variables,
        logs=[e.__dict__ for e in logger.entries],
    )
