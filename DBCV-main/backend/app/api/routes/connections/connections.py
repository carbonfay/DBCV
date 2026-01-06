from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

import app.crud.connection as crud_connection
import app.schemas.connection as schemas_connection
from app.api.dependencies.db import SessionDep
from app.models.connection import ConnectionModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentAdmin, BotAccessChecker
from app.models.access import AccessType

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentAdmin],
    response_model=list[schemas_connection.ConnectionPublic],
)
async def read_connections(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve connections.
    """
    statement = select(ConnectionModel).offset(skip)
    if limit:
        statement = statement.limit(limit)
    return list((await session.scalars(statement)).all())


@router.post(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=schemas_connection.ConnectionPublic,
)
async def create_connections(session: SessionDep, connection_in: schemas_connection.ConnectionCreate, current_user: CurrentUser) -> Any:
    """
    Create a connection.
    """
    await BotAccessChecker._has_access_by_connection_group(session, connection_in.group_id, current_user, AccessType.EDITOR)
    connection = await crud_connection.create_connection(session, connection_in.group_id, connection_in)
    await session.commit()
    await session.refresh(connection)
    return connection


@router.patch(
    "/{connection_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_connection.ConnectionPublic,
)
async def update_connection(
    connection_id: Union[UUID, str], session: SessionDep, connection_in: schemas_connection.ConnectionUpdate, current_user: CurrentUser
) -> Any:
    """
    Update a connection.
    """
    await BotAccessChecker._has_access_by_connection(session, connection_id, current_user, AccessType.EDITOR)
    connection = await crud_connection.update_connection(session, connection_id, connection_in)
    await session.commit()
    await session.refresh(connection)
    return connection


@router.delete("/{connection_id}",
               dependencies=[CurrentDeveloper],
               response_model=Message)
async def delete_connection(session: SessionDep, connection_id: Union[UUID, str], current_user: CurrentUser) -> Message:
    """
    Delete a connection.
    """
    await BotAccessChecker._has_access_by_connection(session, connection_id, current_user, AccessType.EDITOR)
    await crud_connection.delete_connection(session, connection_id)
    await session.commit()
    return Message(message="Connection deleted successfully.")
