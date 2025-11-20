from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.decorators import partial_model
from app.schemas.variables import VariablesPublic, VariablesUpdate
from app.schemas.base import Timestamp
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.user import UserPublic, UserSimple
    from app.schemas.bot import BotPublic, BotSimple, BotSmall
    from app.schemas.message import MessageSimple
    from app.schemas.variables import VariablesUpdate
    from app.schemas.anonymous_user import AnonymousUserSimple


class ChannelBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True
    default_bot_id: Optional[Union[UUID, str]] = None


class ChannelSimple(ChannelBase, Timestamp):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    owner_id: Optional[Union[UUID, str]] = None


class ChannelBuilder(ChannelSimple):
    model_config = ConfigDict(from_attributes=True)
    owner: Optional['UserSimple'] = None
    default_bot: Optional['BotSmall'] = None
    subscribers: List[Union['UserSimple', 'AnonymousUserSimple', 'BotSmall']] = []
    variables: VariablesPublic


class ChannelPublic(ChannelSimple):
    owner: Optional[Union['UserSimple', 'UserPublic']] = None
    default_bot: Optional[Union['BotSimple', 'BotPublic']] = None
    subscribers: List[Union['UserSimple', 'AnonymousUserSimple', 'BotSimple']] = []
    messages: List['MessageSimple'] = []
    variables: VariablesPublic


class ChannelCreate(ChannelBase):
    pass


@partial_model
class ChannelUpdate(ChannelBase):
    variables: Optional['VariablesUpdate'] = None
    pass


class IsSubscriber(BaseModel):
    is_subscriber: bool


def _rebuild_models() -> None:
    for model in (
        ChannelBase,
        ChannelSimple,
        ChannelBuilder,
        ChannelPublic,
        ChannelCreate,
        ChannelUpdate,
        IsSubscriber,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
