from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.block import Block
from app.utils.decorators import partial_model
from app.schemas.base import Timestamp
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.message import MessageSimple
    from app.schemas.bot import BotSimple
    from app.schemas.cron import CronSimple


class EmitterBase(Block):
    name: str
    is_active: Optional[bool] = True
    needs_message_processing: bool = True
    message_id: Optional[Union[UUID, str]] = None
    cron_id: Optional[Union[UUID, str]] = None
    bot_id: Union[UUID, str]


class EmitterSimple(EmitterBase, Timestamp):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]
    job_id: Optional[str] = None


class EmitterPublic(EmitterSimple):
    model_config = ConfigDict(from_attributes=True)
    cron: Optional['CronSimple'] = None
    message: Optional['MessageSimple'] = None


class EmitterCreate(EmitterBase):
    pass


@partial_model
class EmitterUpdate(EmitterBase):
    pass



def _rebuild_models() -> None:
    for model in (
        EmitterBase,
        EmitterSimple,
        EmitterPublic,
        EmitterCreate,
        EmitterUpdate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
