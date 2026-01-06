from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.decorators import partial_model
from app.schemas import register_model_rebuilder


class CronBase(BaseModel):
    name: str
    year: Optional[Union[str, int]] = "*"
    month: Optional[Union[str, int]] = "*"
    day: Optional[Union[str, int]] = "*"
    day_of_week: Optional[Union[str, int]] = "*"
    hour: Optional[Union[str, int]] = "*"
    minute: Optional[Union[str, int]] = "*"
    second: Optional[Union[str, int]] = "*"


class CronSimple(CronBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class CronPublic(CronSimple):
    model_config = ConfigDict(from_attributes=True)


class CronCreate(CronBase):
    pass


@partial_model
class CronUpdate(CronBase):
    pass


def _rebuild_models() -> None:
    for model in (
        CronBase,
        CronSimple,
        CronPublic,
        CronCreate,
        CronUpdate,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
