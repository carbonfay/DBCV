from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

import app.crud.connection_group as crud_connection_group
import app.crud.connection as crud_connection
import app.schemas.connection as schemas_connection_group
from app.api.dependencies.db import SessionDep
from app.models.connection import ConnectionGroupModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, BotAccessChecker
from app.models.access import AccessType

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_connection_group.ConnectionGroupPublic],
)
async def read_connection_groups(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve connection_groups.
    """
    statement = select(ConnectionGroupModel).offset(skip)
    if limit:
        statement = statement.limit(limit)
    return list((await session.scalars(statement)).all())


@router.post(
    "/",
    response_model=schemas_connection_group.ConnectionGroupPublic,
)
async def create_connection_group(session: SessionDep, connection_group_in: schemas_connection_group.ConnectionGroupCreate, current_user: CurrentUser) -> Any:
    """
    Create a connection_group.
    """
    if connection_group_in.step_id:
        await BotAccessChecker._has_access_by_step(session, connection_group_in.step_id, current_user, AccessType.EDITOR)
    if connection_group_in.bot_id:
        await BotAccessChecker._has_access(session, connection_group_in.bot_id, current_user, AccessType.EDITOR)
    connection_group = await crud_connection_group.create_connection_group(session, connection_group_in)
    await session.commit()
    await session.refresh(connection_group)
    connections_in = connection_group_in.connections
    for connection_in in connections_in:
        connection = await crud_connection.create_connection(session, connection_group.id, connection_in)
        await session.commit()
        await session.refresh(connection)
    refresh_attrs = ["connections"]
    if connection_group.request_id:
        refresh_attrs.append("request")
    if connection_group.step_id:
        refresh_attrs.append("step")
    if connection_group.bot_id:
        refresh_attrs.append("bot")
    await session.refresh(connection_group, attribute_names=refresh_attrs)
    return connection_group


@router.patch(
    "/{connection_group_id}",
    response_model=schemas_connection_group.ConnectionGroupPublic,
)
async def update_connection_group(
    connection_group_id: Union[UUID, str], session: SessionDep, connection_group_in: schemas_connection_group.ConnectionGroupUpdate, current_user: CurrentUser
) -> Any:
    """
    Update a connection_group.
    """
    await BotAccessChecker._has_access_by_connection_group(session, connection_group_id, current_user, AccessType.EDITOR)
    connection_group = await crud_connection_group.update_connection_group(session, connection_group_id, connection_group_in)
    await session.commit()
    connections_ids = []
    connections_in = connection_group_in.connections
    for connection_in in connections_in:
        if connection_in.id is None:
            connection = await crud_connection.create_connection(session, connection_group_id, connection_in)
        else:
            connection = await crud_connection.update_connection(session, connection_in.id, connection_in)
        await session.commit()
        await session.refresh(connection)
        connections_ids.append(str(connection.id))
    for connection in connection_group.connections:
        if str(connection.id) not in connections_ids:
            await crud_connection.delete_connection(session, connection.id)
            await session.commit()
    await session.refresh(connection_group)
    return connection_group


@router.delete("/{connection_group_id}",
               response_model=Message)
async def delete_connection_group(session: SessionDep, connection_group_id: Union[UUID, str], current_user: CurrentUser) -> Message:
    """
    Delete a connection_group.
    """
    await BotAccessChecker._has_access_by_connection_group(session, connection_group_id, current_user, AccessType.EDITOR)
    await crud_connection_group.delete_connection_group(session, connection_group_id)
    await session.commit()
    return Message(message="Connection group deleted successfully.")

