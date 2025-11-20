from __future__ import annotations

import json
from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.json_schema import JsonSchemaValue

from app.utils.decorators import partial_model
from app.schemas.subscriber import SubscriberBase
from app.schemas.base import Timestamp
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.user import UserSimple
    from app.schemas.step import StepPublic, StepBase, StepExport
    from app.schemas.connection import ConnectionGroupPublic, ConnectionGroupExport
    from app.schemas.emitter import EmitterPublic
    from app.schemas.note import NotePublic
    from app.schemas.channel import ChannelSimple
    from app.schemas.variables import VariablesUpdate


class BotBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None
    config: Optional[Union[JsonSchemaValue, str]] = None

    @field_validator('config')
    def parse_json_fields(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value


class BotSmall(BotBase, Timestamp, SubscriberBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class BotSimple(BotBase, Timestamp, SubscriberBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    owner_id: Optional[Union[UUID, str]] = None
    first_step_id: Optional[Union[UUID, str]] = None


class BotPublic(BotSimple):
    model_config = ConfigDict(from_attributes=True)
    type: str
    owner: 'UserSimple'
    first_step: Optional['StepPublic'] = None
    steps: List['StepPublic'] = []
    emitters: List['EmitterPublic'] = []
    master_connection_groups: List['ConnectionGroupPublic'] = []
    notes: List['NotePublic'] = []
    channels: List['ChannelSimple'] = []
    variables: Optional['VariablesUpdate'] = None


class BotExport(BotPublic):
    steps: List['StepExport'] = []
    master_connection_groups: List['ConnectionGroupExport'] = []


class BotProcessor(BotSimple):
    first_step: Optional['StepPublic'] = None
    steps: List['StepExport'] = []
    master_connection_groups: List['ConnectionGroupExport'] = []


class BotCreate(BotBase):
    pass


@partial_model
class BotUpdate(BotBase):
    first_step_id: Optional[Union[UUID, str]] = None
    variables: Optional['VariablesUpdate'] = None

def _rebuild_models() -> None:
    for model in (
        BotBase,
        BotSmall,
        BotSimple,
        BotPublic,
        BotExport,
        BotProcessor,
        BotCreate,
        BotUpdate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
