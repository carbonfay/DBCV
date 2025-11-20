from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.request import RequestModel
from app.schemas import request as schemas_request
from app.crud.utils import is_object_unique


async def check_request_unique(
        session: AsyncSession,
        request_in: schemas_request.RequestBase,
        exclude_id: UUID | str | None = None,
) -> None:
    if not await is_request_unique(session, request_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The request with the given name already exists.",
        )


async def is_request_unique(
        session: AsyncSession,
        request_in: schemas_request.RequestBase | schemas_request.RequestUpdate,
        exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        RequestModel,
        request_in,
        unique_fields=("name",),
        exclude_id=exclude_id,
    )


async def get_request(session: AsyncSession, request_id: UUID | str,
                      eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[RequestModel]:
    request = await RequestModel.get_obj(session, request_id, eager_relationships)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found.")
    return request


async def create_request(
        session: AsyncSession,
        request_in: schemas_request.RequestCreate,
        *,
        owner_id: UUID | str,
) -> RequestModel:
    db_obj = RequestModel(
        **request_in.model_dump(),
        owner_id=owner_id,
    )
    session.add(db_obj)
    return db_obj


async def update_request(
        session: AsyncSession,
        request_id: UUID | str,
        request_in: schemas_request.RequestUpdate,
) -> Type[RequestModel]:
    request = await get_request(session, request_id)
    for key, value in request_in.model_dump(exclude_unset=True).items():
        setattr(request, key, value)
    return request


async def delete_request(session: AsyncSession, request_id: UUID | str) -> None:
    await session.delete(await get_request(session, request_id))
