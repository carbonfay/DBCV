from __future__ import annotations

import json
from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.types import Json, JsonSchemaValue

from app.utils.decorators import partial_model
from app.schemas.base import Timestamp
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.user import UserSimple
    from app.schemas.widget import WidgetPublic
    from app.schemas.bot import BotSimple, BotSmall
    from app.schemas.attachment import AttachmentSimple
    from app.schemas.step import StepPublic, StepTemplate
    from app.schemas.channel import ChannelSimple
    from app.schemas.anonymous_user import AnonymousUserSimple


class Message(BaseModel):
    message: str


class MessageBase(BaseModel):
    text: Optional[str] = None
    params: Optional[JsonSchemaValue] = None


class MessageRelated(MessageBase):
    recipient_id: Optional[Union[UUID, str]] = None
    sender_id: Optional[Union[UUID, str]] = None
    widget_id: Optional[Union[str, UUID]] = None


class MessagePrivateBase(MessageRelated):
    step_id: Optional[Union[str, UUID]] = None
    channel_id: Optional[Union[str, UUID]] = None


class MessageSimple(MessageRelated, Timestamp):
    model_config = ConfigDict(from_attributes=True)
    channel_id: Optional[Union[str, UUID]] = None
    id: Union[UUID, str]


class MessagePublic(MessageSimple):
    model_config = ConfigDict(from_attributes=True)
    widget: Optional['WidgetPublic'] = None
    attachments: List['AttachmentSimple'] = []
    recipient: Optional[Union['UserSimple', 'BotSmall', 'AnonymousUserSimple']] = None
    sender: Optional[Union['UserSimple', 'BotSmall', 'AnonymousUserSimple']] = None


class MessageAll(MessageSimple):
    recipient: Optional[Union['UserSimple', 'BotSimple', 'AnonymousUserSimple']] = None
    sender: Optional[Union['UserSimple', 'BotSimple', 'AnonymousUserSimple']] = None
    widget: Optional['WidgetPublic'] = None
    attachments: List['AttachmentSimple'] = []


class MessageCreate(MessageRelated):
    channel_id: Optional[Union[str, UUID]] = None

    def is_all_none(self) -> bool:
        return (
            self.recipient_id is None
            and self.sender_id is None
            and self.widget_id is None
            and self.params is None
            and (self.text == "" or self.text is None)
        )


class MessagePrivate(MessagePublic):
    step: Optional['StepPublic'] = None
    channel: Optional['ChannelSimple'] = None


class MessagePrivateCreate(MessagePrivateBase):
    pass


@partial_model
class MessageUpdate(MessageRelated):
    pass


@partial_model
class MessagePrivateUpdate(MessagePrivateBase):
    pass


class MessageSubstitute(MessageSimple):
    model_config = ConfigDict(from_attributes=True)
    widget: Optional['WidgetPublic'] = None
    attachments: List['AttachmentSimple'] = []
    params: Optional[Union[Json, JsonSchemaValue]] = None

    @field_validator('params')
    def parse_json_field2(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value


class MessageTemplate(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    ...


def _rebuild_models() -> None:
    for model in (
        Message,
        MessageBase,
        MessageRelated,
        MessagePrivateBase,
        MessageSimple,
        MessagePublic,
        MessageAll,
        MessageCreate,
        MessagePrivate,
        MessagePrivateCreate,
        MessageUpdate,
        MessagePrivateUpdate,
        MessageSubstitute,
        MessageTemplate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
