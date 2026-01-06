from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from app.models.bot import BotModel
from app.models.message import MessageModel
from app.models.step import StepModel

import app.crud.widget as crud_widget
import app.schemas.widget as schemas_widget
from app.api.dependencies.db import SessionDep
from app.models.widget import WidgetModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentDeveloperDep

router = APIRouter()


async def _attach_bots_to_widgets(session: SessionDep, widgets: list[WidgetModel]) -> None:
    if not widgets:
        return
    widget_ids = [w.id for w in widgets]
    rows = await session.execute(
        select(MessageModel.widget_id, BotModel)
        .join(StepModel, MessageModel.step_id == StepModel.id)
        .join(BotModel, StepModel.bot_id == BotModel.id)
        .where(MessageModel.widget_id.in_(widget_ids))
    )
    mapping: dict[str, list[BotModel]] = {}
    for wid, bot in rows.all():
        key = str(wid)
        lst = mapping.setdefault(key, [])
        if bot not in lst:
            lst.append(bot)
    for w in widgets:
        w.__dict__["bots"] = mapping.get(str(w.id), [])


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_widget.WidgetPublic],
)
async def read_widgets(
        session: SessionDep,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve widgets (only templates, is_render=False).
    """
    widgets = await WidgetModel.get_all(session, skip, limit,
                                        eager_relationships=WidgetModel.default_eager_relationships,
                                        is_render=False)
    await _attach_bots_to_widgets(session, widgets)  # type: ignore
    return widgets


@router.get(
    "/all",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_widget.WidgetPublic],
)
async def read_all_widgets(
        session: SessionDep,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve all widgets (templates and rendered widgets).
    """
    widgets = await WidgetModel.get_all(session, skip, limit,
                                        eager_relationships=WidgetModel.default_eager_relationships, )
    await _attach_bots_to_widgets(session, widgets)  # type: ignore
    return widgets


@router.get(
    "/rendered",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_widget.WidgetPublic],
)
async def read_rendered_widgets(
        session: SessionDep,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve rendered widgets (is_render=True).
    """
    widgets = await WidgetModel.get_all(session, skip, limit,
                                        eager_relationships=WidgetModel.default_eager_relationships,
                                        is_render=True)
    await _attach_bots_to_widgets(session, widgets)  # type: ignore
    return widgets


@router.get(
    "/{widget_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_widget.WidgetPublic,
)
async def read_widget(
        widget_id: Union[UUID, str],
        session: SessionDep,
) -> Any:
    """
    Get a widget by id.
    """
    widget = await WidgetModel.get_obj(session, widget_id, eager_relationships=WidgetModel.default_eager_relationships)
    await _attach_bots_to_widgets(session, [widget])
    return widget


@router.post(
    "/",
    response_model=schemas_widget.WidgetPublic,
)
async def create_widget(session: SessionDep, widget_in: schemas_widget.WidgetCreate,
                        current_user: CurrentDeveloperDep) -> Any:
    """
    Create a widget.
    """
    await crud_widget.check_widget_unique(session, widget_in)
    widget = await crud_widget.create_widget(session, widget_in, current_user)
    await session.commit()
    await session.refresh(widget, ["owner"])
    await _attach_bots_to_widgets(session, [widget])
    return widget


@router.patch(
    "/{widget_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_widget.WidgetPublic,
)
async def update_widget(
        widget_id: Union[UUID, str], session: SessionDep, widget_in: schemas_widget.WidgetUpdate
) -> Any:
    """
    Update a widget.
    """
    widget = await crud_widget.update_widget(session, widget_id, widget_in)
    await session.commit()
    await session.refresh(widget, ["owner"])
    return widget


@router.delete("/{widget_id}",
               dependencies=[CurrentDeveloper],
               response_model=Message)
async def delete_widget(session: SessionDep, widget_id: Union[UUID, str]) -> Message:
    """
    Delete a widget.
    """
    await crud_widget.delete_widget(session, widget_id)
    await session.commit()
    return Message(message="Widget deleted successfully.")
