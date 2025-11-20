import uuid
from typing import Optional, List, Union
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
import enum
from sqlalchemy import Integer, Enum
from sqlalchemy.dialects.postgresql import JSON
import json
from app.models.block import Block


class EmitterModel(BaseModel, Block):
    __tablename__ = "emitter"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    job_id: Mapped[Optional[str]]
    cron_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("cron.id"), nullable=True)
    cron: Mapped[Optional["CronModel"]] = relationship("CronModel", back_populates="emitters", foreign_keys=cron_id, lazy="selectin", load_on_pending=True)
    message_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("message.id"), nullable=True)
    message: Mapped[Optional["MessageModel"]] = relationship("MessageModel", back_populates="emitter", foreign_keys=message_id, lazy="selectin", load_on_pending=True)

    bot_id: Mapped[UUID] = mapped_column(ForeignKey("bot.id"))
    bot: Mapped["BotModel"] = relationship("BotModel", back_populates="emitters", foreign_keys=bot_id, lazy="select", load_on_pending=True)

    needs_message_processing: Mapped[bool] = mapped_column(default=True, server_default="true")

    default_eager_relationships = {
        'message': {},
        'cron': {}
    }

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, name={self.name!r})"

    def __repr__(self):
        return str(self)
