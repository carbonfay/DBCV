from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.widget import WidgetModel
from app.schemas import widget as schemas_widget
from app.crud.utils import is_object_unique


async def check_widget_unique(
    session: AsyncSession,
    widget_in: schemas_widget.WidgetBase,
    exclude_id: UUID | str | None = None,
) -> None:
    if not await is_widget_unique(session, widget_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The widget with the given name already exists.",
        )


async def is_widget_unique(
    session: AsyncSession,
    widget_in: schemas_widget.WidgetBase | schemas_widget.WidgetUpdate,
    exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        WidgetModel,
        widget_in,
        unique_fields=(),
        exclude_id=exclude_id,
    )


async def get_widget(session: AsyncSession, widget_id: UUID | str,
                     eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[WidgetModel]:
    widget = await WidgetModel.get_obj(session, widget_id, eager_relationships)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found.")
    return widget


async def create_widget(
    session: AsyncSession, widget_in: schemas_widget.WidgetCreate, owner: CurrentUser | None = None,
) -> WidgetModel:
    db_obj = WidgetModel(
        **widget_in.model_dump(),
        owner_id=owner.id if owner else None,
    )
    session.add(db_obj)
    return db_obj


async def update_widget(
    session: AsyncSession,
    widget_id: UUID | str,
    widget_in: schemas_widget.WidgetUpdate,
) -> Type[WidgetModel]:
    widget = await get_widget(session, widget_id)
    for key, value in widget_in.model_dump(exclude_unset=True).items():
        setattr(widget, key, value)
    return widget


async def delete_widget(session: AsyncSession, widget_id: UUID | str) -> None:
    await session.delete(await get_widget(session, widget_id))


