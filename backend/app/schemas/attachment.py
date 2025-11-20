from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.decorators import partial_model
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.message import MessageSimple


class AttachmentBase(BaseModel):
    message_id: Optional[Union[UUID, str]] = None


class AttachmentSimple(AttachmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    content_type: Optional[str] = None
    url: str


class AttachmentPublic(AttachmentSimple):
    model_config = ConfigDict(from_attributes=True)
    message: Optional['MessageSimple'] = None


def _rebuild_models() -> None:
    from app.schemas.message import MessageSimple

    globals()['MessageSimple'] = MessageSimple
    for model in (
        AttachmentBase,
        AttachmentSimple,
        AttachmentPublic,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
