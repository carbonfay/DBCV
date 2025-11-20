from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.utils.decorators import partial_model
from app.schemas.block import Block
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.message import MessagePublic, MessageTemplate
    from app.schemas.connection import ConnectionPublic, ConnectionGroupPublic, ConnectionGroupExport, ConnectionGroupTemplate
    from app.schemas.templates import TemplateInstancePublic


class StepBase(Block):
    name: str
    is_proxy: bool
    description: Optional[str] = None
    timeout_after: Optional[int] = None


class StepRelation(StepBase):
    bot_id: Union[UUID, str]
    template_instance_id: Optional[Union[UUID, str]] = None


class StepSimple(StepRelation):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class StepPublic(StepSimple):
    model_config = ConfigDict(from_attributes=True)
    message: Optional['MessagePublic'] = None
    connection_groups: List['ConnectionGroupPublic'] = []
    template_instance: Optional['TemplateInstancePublic'] = None


class StepExport(StepSimple):
    message: Optional['MessagePublic'] = None
    connection_groups: List['ConnectionGroupExport'] = []
    template_instance: Optional['TemplateInstancePublic'] = None


class StepCreate(StepRelation):
    ...


@partial_model
class StepUpdate(StepRelation):
    pass


class StepTemplate(StepBase):
    id: Union[UUID, str]
    message: Optional['MessageTemplate'] = None
    connection_groups: List['ConnectionGroupTemplate'] = []

    @field_validator('id')
    def parse_json_fields(cls, value):
        if isinstance(value, UUID):
            try:
                return str(value)
            except Exception:
                return value
        return value


def _rebuild_models() -> None:
    for model in (
        StepBase,
        StepRelation,
        StepSimple,
        StepPublic,
        StepExport,
        StepCreate,
        StepUpdate,
        StepTemplate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
