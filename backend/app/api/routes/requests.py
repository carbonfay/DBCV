from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis
from sqlalchemy import select
from app.models.bot import BotModel
from app.models.connection import ConnectionGroupModel
from app.models.step import StepModel

import app.crud.request as crud_request
import app.crud.bot as crud_bot
import app.schemas.request as schemas_request
from app.api.dependencies.db import SessionDep
from app.auth.credentials_resolver import CredentialsResolver
from app.auth.service import AuthService
from app.config import settings
from app.engine.bot_processor import ConnectionResponseHandler
from app.engine.variables import variable_substitution_pydantic
from app.managers.data_manager import DataManager
from app.models.request import RequestModel
from app.schemas.bot import BotProcessor
from app.schemas.connection import ConnectionGroupExport
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentDeveloperDep
from app.loggers import BotLogger


router = APIRouter()


async def _attach_bots_to_requests(session: SessionDep, requests: list[RequestModel]) -> None:
    if not requests:
        return
    request_ids = [r.id for r in requests]
    direct_rows = await session.execute(
        select(ConnectionGroupModel.request_id, BotModel)
        .join(BotModel, ConnectionGroupModel.bot_id == BotModel.id)
        .where(ConnectionGroupModel.request_id.in_(request_ids))
    )
    via_step_rows = await session.execute(
        select(ConnectionGroupModel.request_id, BotModel)
        .join(StepModel, ConnectionGroupModel.step_id == StepModel.id)
        .join(BotModel, StepModel.bot_id == BotModel.id)
        .where(ConnectionGroupModel.request_id.in_(request_ids))
    )
    mapping: dict[str, list[BotModel]] = {}
    for req_id, bot in list(direct_rows.all()) + list(via_step_rows.all()):
        key = str(req_id)
        lst = mapping.setdefault(key, [])
        if bot not in lst:
            lst.append(bot)
    for r in requests:
        r.__dict__["bots"] = mapping.get(str(r.id), [])

@router.get(
    "/my",
    response_model=list[schemas_request.RequestPublic],
)
async def read_my_requests(
        session: SessionDep,
        current_user: CurrentUser,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve requests owned by the current user.
    """
    requests = await RequestModel.get_all(
        session,
        skip,
        limit,
        RequestModel.default_eager_relationships,
        owner_id=current_user.id,
    )
    await _attach_bots_to_requests(session, requests)
    return requests


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_request.RequestPublic],
)
async def read_requests(
        session: SessionDep,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve requests.
    """
    requests = await RequestModel.get_all(session, skip, limit, RequestModel.default_eager_relationships)
    await _attach_bots_to_requests(session, requests)
    return requests


@router.get(
    "/{request_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_request.RequestPublic,
)
async def read_request(
        request_id: Union[UUID, str],
        session: SessionDep,
) -> Any:
    """
    Get a request by id.
    """
    request = await RequestModel.get_obj(session, request_id)
    await _attach_bots_to_requests(session, [request])
    return request


@router.post(
    "/",
    response_model=schemas_request.RequestPublic,
)
async def create_request(session: SessionDep, request_in: schemas_request.RequestCreate, current_user: CurrentDeveloperDep) -> Any:
    """
    Create a request.
    """
    request = await crud_request.create_request(session, request_in, owner_id=current_user.id)
    await session.commit()
    await session.refresh(request)
    await _attach_bots_to_requests(session, [request])
    return request


@router.patch(
    "/{request_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_request.RequestPublic,
)
async def update_request(
        request_id: Union[UUID, str], session: SessionDep, request_in: schemas_request.RequestUpdate
) -> Any:
    """
    Update a request.
    """
    request = await crud_request.update_request(session, request_id, request_in)
    await session.commit()
    await session.refresh(request)
    await _attach_bots_to_requests(session, [request])
    return request


@router.delete("/{request_id}",
               dependencies=[CurrentDeveloper],
               response_model=Message)
async def delete_request(session: SessionDep, request_id: Union[UUID, str]) -> Message:
    """
    Delete a request.
    """
    await crud_request.delete_request(session, request_id)
    await session.commit()
    return Message(message="Request deleted successfully.")


@router.post(
    "/{request_id}/execute",
    dependencies=[CurrentDeveloper],
    response_model=schemas_request.ExecuteRequestOut,
)
async def execute_request(
    request_id: Union[UUID, str],
    session: SessionDep,
    request_in: schemas_request.ExecuteRequestIn,
) -> Any:
    """
    Выполняет сохранённый Request с подстановкой переменных.
    """

    request = await crud_request.get_request(session, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    ctx = request_in.variables

    try:
        prepared: schemas_request.RequestSubstitute = await variable_substitution_pydantic(
            schemas_request.RequestSubstitute.model_validate(request.__dict__),
            context=ctx,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Variable substitution error: {e}")

    if request_in.dry_run:
        return schemas_request.ExecuteRequestOut(
            result={"dry_run": True},
            prepared_request=prepared.model_dump(),
        )

    dm = DataManager(Redis.from_url(settings.REDIS_URL), session.bind)
    bot = BotProcessor(**(await dm.get_bot(request_in.bot_id)))
    resolver = CredentialsResolver(dm)
    auth_service = AuthService(resolver)

    handler = ConnectionResponseHandler(bot, auth_service, dm)
    fictional_connection = ConnectionGroupExport(
        id="fake",
        request=schemas_request.RequestPublic(**request.__dict__)
    )

    try:
        result = await handler.handle(
            connection_group=fictional_connection,
            context=request_in.variables,
            all_variables=ctx,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Execution error: {e}")

    if result is None:
        raise HTTPException(status_code=502, detail="Upstream returned no result")

    return schemas_request.ExecuteRequestOut(
        result=result,
        prepared_request=prepared.model_dump()
    )
