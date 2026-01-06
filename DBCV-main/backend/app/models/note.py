import uuid
from typing import Optional, List, Union
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from sqlalchemy.types import JSON
from app.models.block import Block


class NoteModel(BaseModel, Block):
    __tablename__ = "note"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)

    text: Mapped[str | None]

    bot_id: Mapped[UUID] = mapped_column(ForeignKey("bot.id"), nullable=False)
    bot: Mapped["BotModel"] = relationship("BotModel", back_populates="notes", foreign_keys=bot_id, lazy="select", load_on_pending=True)

    step_id: Mapped[UUID | None] = mapped_column(ForeignKey("step.id"), nullable=True)
    step: Mapped["StepModel"] = relationship("StepModel", back_populates="notes", foreign_keys=step_id, lazy="select", load_on_pending=True)
