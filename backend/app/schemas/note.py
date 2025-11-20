from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.decorators import partial_model
from app.schemas.block import Block
from app.schemas.base import Timestamp


class NoteBase(Block):
    text: str
    bot_id: Union[UUID, str]
    step_id: Optional[Union[UUID, str]] = None


class NoteSimple(NoteBase, Timestamp):
    model_config = ConfigDict(from_attributes=True)
    id: Union[UUID, str]


class NotePublic(NoteSimple):
    ...


class NoteCreate(NoteBase):
    ...


@partial_model
class NoteUpdate(NoteBase):
    pass
