from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, RootModel

from app.schemas import register_model_rebuilder
from app.schemas.block import Block

if TYPE_CHECKING:
    from app.schemas.step import StepTemplate
    from app.schemas.request import RequestTemplate
    from app.schemas.template_group import TemplateGroupRef


class DSLSchema(BaseModel):
    type: str
    properties: Dict[str, Any]
    required: List[str] = []


class FieldMapping(BaseModel):
    path: Optional[str] = None
    default: Any = None


class MappingSchema(RootModel[Dict[str, Union[FieldMapping, 'MappingSchema']]]):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TemplateBaseSchemas(BaseModel):
    name: str
    description: Optional[str] = None
    variables: Dict[str, Any] = {}


class TemplateBase(TemplateBaseSchemas):
    inputs: DSLSchema
    outputs: DSLSchema
    bot_id: Optional[Union[str, UUID]] = None

    class Config:
        json_encoders = {UUID: str}


class TemplateSteps(BaseModel):
    first_step_id: str
    steps: List['StepTemplate']


class TemplateSimple(TemplateBase, TemplateSteps):
    id: Union[str, UUID]


class TemplatePublic(TemplateSimple):
    group: Optional['TemplateGroupRef'] = None


class TemplateCreateData(TemplateBase):
    step_ids: List[str] = []
    first_step_id: str


class TemplateUpdateData(TemplateBase):
    step_ids: List[str] = []
    first_step_id: str


class TemplateCreate(TemplateBase, TemplateSteps):
    owner_id: Union[str, UUID]


class TemplateUpdate(TemplateBase, TemplateSteps):
    ...


class TemplateInstance(TemplateBaseSchemas, TemplateSteps):
    inputs_mapping: MappingSchema
    outputs_mapping: MappingSchema


class TemplateInstanceSimple(TemplateInstance):
    id: Union[str, UUID]


class TemplateInstancePublic(TemplateInstanceSimple):
    model_config = ConfigDict(from_attributes=True)
    ...


class TemplateInstanceCreateData(BaseModel):
    template_id: Union[str, UUID]
    inputs_mapping: MappingSchema
    outputs_mapping: MappingSchema
    variables: Dict[str, Any] = {}


class TemplateInstanceCreateAndInsert(TemplateInstanceCreateData, Block):
    ...


class TemplateInstanceCreate(TemplateBaseSchemas, TemplateInstanceCreateData, TemplateSteps):
    ...


class TemplateInstanceUpdate(TemplateBaseSchemas):
    ...



def _rebuild_models() -> None:
    MappingSchema.model_rebuild()


register_model_rebuilder(_rebuild_models)
