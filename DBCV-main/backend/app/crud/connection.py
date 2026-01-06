from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.connection import ConnectionModel
from app.schemas import connection as schemas_connection
from app.crud.utils import is_object_unique


async def get_connection(session: AsyncSession, connection_id: UUID | str,
                         eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[ConnectionModel]:
    connection = await ConnectionModel.get_obj(session, connection_id, eager_relationships)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found.")
    return connection


async def create_connection(
    session: AsyncSession, group_id, connection_in: schemas_connection.ConnectionCreate,
) -> ConnectionModel:
    db_obj = ConnectionModel(
        **connection_in.model_dump(),
        group_id=group_id
    )
    session.add(db_obj)
    return db_obj


async def update_connection(
    session: AsyncSession,
    connection_id: UUID | str,
    connection_in: schemas_connection.ConnectionUpdate | schemas_connection.ConnectionUpdateWithId,
) -> Type[ConnectionModel]:
    connection = await get_connection(session, connection_id)
    for key, value in connection_in.model_dump(exclude_unset=True, exclude={"id", }).items():
        setattr(connection, key, value)
    return connection


async def delete_connection(session: AsyncSession, connection_id: UUID | str) -> None:
    await session.delete(await get_connection(session, connection_id))


