from __future__ import annotations

from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.types import JsonSchemaValue

from app.utils.decorators import partial_model
from app.schemas import register_model_rebuilder
from app.schemas.step import StepPublic, StepSimple
from app.schemas.bot import BotBase, BotPublic
from app.schemas.request import RequestCreate, RequestPublic, RequestTemplate
from app.models.connection import SearchType


class ConnectionBase(BaseModel):
    priority: int = 0
    next_step_id: Union[UUID, str]
    rules: Optional[Union[JsonSchemaValue, str]] = None
    filters: Optional[Union[JsonSchemaValue, str]] = None


class ConnectionSimple(ConnectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    group_id: Union[UUID, str]


class ConnectionPublic(ConnectionSimple):
    model_config = ConfigDict(from_attributes=True)
    next_step: StepPublic


class ConnectionExport(ConnectionSimple):
    model_config = ConfigDict(from_attributes=True)
    next_step: StepSimple


class ConnectionCreate(ConnectionBase):
    pass


@partial_model
class ConnectionUpdate(ConnectionBase):
    pass


@partial_model
class ConnectionUpdateWithId(ConnectionBase):
    id: Optional[Union[UUID, str]] = None


class ConnectionTemplate(ConnectionBase):
    model_config = ConfigDict(from_attributes=True)

    @field_validator('next_step_id')
    def parse_json_fields(cls, value):
        if isinstance(value, UUID):
            try:
                return str(value)
            except Exception:
                return value
        return value


class ConnectionGroupBase(BaseModel):
    search_type: SearchType = SearchType.message
    priority: int = 0
    code: Optional[str] = None
    variables: Optional[str] = None


class ConnectionGroupRelated(ConnectionGroupBase):
    request_id: Optional[Union[UUID, str]] = None
    step_id: Optional[Union[UUID, str]] = None
    bot_id: Optional[Union[UUID, str]] = None
    integration_id: Optional[str] = None
    integration_config: Optional[Union[JsonSchemaValue, dict]] = None


class ConnectionGroupSimple(ConnectionGroupRelated):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class ConnectionGroupPublic(ConnectionGroupSimple):
    model_config = ConfigDict(from_attributes=True)
    request: Optional[RequestPublic] = None
    connections: List[ConnectionSimple] = []


class ConnectionGroupAll(ConnectionGroupSimple):
    model_config = ConfigDict(from_attributes=True)
    step: StepPublic
    bot: BotPublic


class ConnectionGroupExport(ConnectionGroupSimple):
    model_config = ConfigDict(from_attributes=True)
    request: Optional[RequestPublic] = None
    connections: List[ConnectionExport] = []
    step: Optional[StepSimple] = None
    bot: Optional[BotBase] = None
    integration_id: Optional[str] = None
    integration_config: Optional[Union[JsonSchemaValue, dict]] = None


class ConnectionGroupCreate(ConnectionGroupRelated):
    connections: List[ConnectionCreate] = []


@partial_model
class ConnectionGroupUpdate(ConnectionGroupRelated):
    connections: List[ConnectionUpdateWithId] = []


class ConnectionGroupTemplate(ConnectionGroupBase):
    model_config = ConfigDict(from_attributes=True)
    request: Optional[RequestTemplate] = None
    connections: List[ConnectionTemplate] = []



def _rebuild_models() -> None:
    for model in (
        ConnectionBase,
        ConnectionSimple,
        ConnectionPublic,
        ConnectionExport,
        ConnectionCreate,
        ConnectionUpdate,
        ConnectionUpdateWithId,
        ConnectionTemplate,
        ConnectionGroupBase,
        ConnectionGroupRelated,
        ConnectionGroupSimple,
        ConnectionGroupPublic,
        ConnectionGroupAll,
        ConnectionGroupExport,
        ConnectionGroupCreate,
        ConnectionGroupUpdate,
        ConnectionGroupTemplate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
