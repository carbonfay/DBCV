from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.user import UserSimple


class TemplateGroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class TemplateGroupRef(TemplateGroupBase):
    id: UUID
    owner: Optional['UserSimple'] = None


class TemplateInGroup(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None


class TemplateGroupSimple(TemplateGroupBase):
    id: UUID
    owner: Optional['UserSimple'] = None
    templates: list[TemplateInGroup] = []


class TemplateGroupCreate(TemplateGroupBase):
    pass


class TemplateGroupUpdate(TemplateGroupBase):
    pass


class TemplateGroupPublic(TemplateGroupSimple):

    class Config:
        from_attributes = True


class TemplateGroupBulkAdd(BaseModel):
    template_ids: list[UUID]



def _rebuild_models() -> None:
    for model in (
        TemplateGroupBase,
        TemplateGroupRef,
        TemplateInGroup,
        TemplateGroupSimple,
        TemplateGroupCreate,
        TemplateGroupUpdate,
        TemplateGroupPublic,
        TemplateGroupBulkAdd,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
