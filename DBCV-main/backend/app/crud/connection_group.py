from typing import Type, Optional, Any, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.connection import ConnectionGroupModel
from app.schemas import connection as schemas_connection


async def get_connection_group(session: AsyncSession, connection_group_id: UUID | str,
                               eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[ConnectionGroupModel]:
    connection = await ConnectionGroupModel.get_obj(session, connection_group_id, eager_relationships)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection group not found.")
    return connection


async def create_connection_group(
    session: AsyncSession, connection_group_in: schemas_connection.ConnectionGroupCreate,
) -> ConnectionGroupModel:
    db_obj = ConnectionGroupModel(
        **connection_group_in.model_dump(exclude={"connections", }),
    )
    session.add(db_obj)
    return db_obj


async def update_connection_group(
    session: AsyncSession,
    connection_group_id: UUID | str,
    connection_group_in: schemas_connection.ConnectionGroupUpdate,
) -> Type[ConnectionGroupModel]:
    connection = await get_connection_group(session, connection_group_id)
    for key, value in connection_group_in.model_dump(exclude_unset=True, exclude={"connections", }).items():
        setattr(connection, key, value)
    return connection


async def delete_connection_group(session: AsyncSession, connection_group_id: UUID | str) -> None:
    await session.delete(await get_connection_group(session, connection_group_id))


