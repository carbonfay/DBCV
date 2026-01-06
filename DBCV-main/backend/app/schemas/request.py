from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.types import JsonSchemaValue, Json

from app.utils.decorators import partial_model
from app.schemas.base import Timestamp
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.user import UserSimple


class RequestBase(BaseModel):
    name: str
    content: Optional[str] = None
    params: Optional[Union[JsonSchemaValue, str]] = None
    data: Optional[Union[JsonSchemaValue, str]] = None
    json_field: Optional[Union[JsonSchemaValue, str]] = None
    request_url: str
    method: str
    headers: Optional[str] = None
    url_params: Optional[Union[JsonSchemaValue, str]] = None
    attachments: Optional[str] = None
    proxies: Optional[str] = None


class RequestSimple(RequestBase, Timestamp):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    owner_id: Optional[Union[UUID, str]] = None


class BotRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    name: str


class RequestPublic(RequestSimple):
    model_config = ConfigDict(from_attributes=True)
    owner: Optional['UserSimple'] = None
    bots: list[BotRef] = []


class RequestCreate(RequestBase):
    pass


@partial_model
class RequestUpdate(RequestBase):
    pass


class RequestTemplate(RequestBase):
    model_config = ConfigDict(from_attributes=True)
    pass


class RequestSubstitute(RequestBase):
    params: Optional[Union[Json, JsonSchemaValue]] = None
    json_field: Optional[Union[Json, JsonSchemaValue]] = None
    headers: Optional[Union[Json, str, JsonSchemaValue]] = None
    data: Optional[Union[Json, JsonSchemaValue]] = None
    attachments: Optional[Union[str, list, dict]] = None

    @field_validator('params', 'json_field', 'headers', 'data', 'attachments')
    def parse_json_fields(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value


class ExecuteRequestIn(BaseModel):
    # Context variables in format {"bot": {...}, "channel": {...}, "session": {...}, "user": {...}}
    variables: Dict[str, Any] = Field(default_factory=dict)
    bot_id: Optional[Union[UUID, str]] = None
    # Dry-run: perform substitution only, skip real HTTP call
    dry_run: bool = False


class ExecuteRequestOut(BaseModel):
    result: Any
    prepared_request: Dict[str, Any]



def _rebuild_models() -> None:
    for model in (
        RequestBase,
        RequestSimple,
        RequestPublic,
        RequestCreate,
        RequestUpdate,
        RequestTemplate,
        RequestSubstitute,
        ExecuteRequestIn,
        ExecuteRequestOut,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
