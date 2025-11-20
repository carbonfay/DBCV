from typing import Any, Mapping

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import exists, or_


async def is_object_unique(
    session: AsyncSession,
    model: type[DeclarativeBase],
    data: BaseModel | Mapping[str, Any],
    unique_fields: tuple[str, ...],
    exclude_id: int | None = None,
) -> bool:
    if getattr(model, "id") is None:
        raise ValueError(f"{model.__tablename__} does not have id field.")
    data = data.model_dump(exclude_unset=True) if isinstance(data, BaseModel) else data

    fields_to_check = [field for field in unique_fields if field in data]
    if not fields_to_check:
        return True  # Data has no unique fields

    ex = exists().where(
        or_(*[getattr(model, field) == data[field] for field in fields_to_check])
    )
    if exclude_id is not None:
        ex = ex.where(getattr(model, "id") != exclude_id)
    return not await session.scalar(select(ex))
