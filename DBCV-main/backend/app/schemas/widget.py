from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.decorators import partial_model
from app.schemas.base import Timestamp
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.bot import BotSmall
    from app.schemas.user import UserSimple


class WidgetBase(BaseModel):
    name: str
    description: str
    body: str
    css: str
    js: str
    is_render: bool = False


class WidgetSimple(WidgetBase, Timestamp):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | str
    owner_id: UUID | str | None = None
    parent_widget_id: UUID | str | None = None


class WidgetPublic(WidgetSimple):
    bots: list['BotSmall'] = []
    owner: Optional['UserSimple'] = None


class WidgetCreate(WidgetBase):
    pass


@partial_model
class WidgetUpdate(WidgetBase):
    pass



def _rebuild_models() -> None:
    for model in (
        WidgetBase,
        WidgetSimple,
        WidgetPublic,
        WidgetCreate,
        WidgetUpdate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
