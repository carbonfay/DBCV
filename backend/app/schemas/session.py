from __future__ import annotations

from typing import TYPE_CHECKING, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.decorators import partial_model
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.user import UserPublic
    from app.schemas.bot import BotPublic
    from app.schemas.channel import ChannelPublic
    from app.schemas.step import StepPublic


class SessionBase(BaseModel):
    user_id: Union[UUID, str]
    bot_id: Union[UUID, str]
    channel_id: Union[UUID, str]
    step_id: Union[UUID, str]


class SessionSimple(SessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class SessionPublic(SessionBase):
    id: Union[UUID, str]
    model_config = ConfigDict(from_attributes=True)
    user: 'UserPublic'
    bot: 'BotPublic'
    channel: 'ChannelPublic'
    step: 'StepPublic'


class SessionCreate(SessionBase):
    pass


@partial_model
class SessionUpdate(SessionBase):
    pass



def _rebuild_models() -> None:
    for model in (
        SessionBase,
        SessionSimple,
        SessionPublic,
        SessionCreate,
        SessionUpdate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
