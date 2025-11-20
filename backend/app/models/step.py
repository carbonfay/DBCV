import uuid
from typing import Optional, List, Union
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from app.models.block import Block


class StepModel(BaseModel, Block):
    __tablename__ = "step"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    timeout_after: Mapped[Optional[int]] = mapped_column(default=None, nullable=True)

    bot_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("bot.id"), nullable=True)
    bot: Mapped[Optional["BotModel"]] = relationship("BotModel", back_populates="steps", foreign_keys=bot_id, lazy="select", load_on_pending=True)

    is_proxy: Mapped[bool] = mapped_column(default=False)

    message: Mapped[Union["MessageModel", None]] = relationship("MessageModel", back_populates="step", lazy="selectin", load_on_pending=True, foreign_keys="MessageModel.step_id", uselist=False, cascade="all,delete")

    connection_groups: Mapped[List["ConnectionGroupModel"]] = relationship(back_populates='step', uselist=True, foreign_keys="[ConnectionGroupModel.step_id]", lazy="selectin", load_on_pending=True, cascade="all,delete")
    back_connections: Mapped[List["ConnectionModel"]] = relationship(back_populates='next_step', uselist=True, foreign_keys="[ConnectionModel.next_step_id]", lazy="select", load_on_pending=True, cascade="all,delete")

    notes: Mapped[List["NoteModel"]] = relationship("NoteModel", back_populates="step", foreign_keys="[NoteModel.step_id]", lazy="select", load_on_pending=True, uselist=True)

    template_instance_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("template_instance.id", ondelete="SET NULL"), nullable=True)
    template_instance: Mapped[Optional["TemplateInstanceModel"]] = relationship("TemplateInstanceModel", foreign_keys=template_instance_id, lazy="selectin", load_on_pending=True, cascade="all,delete")

    simple_eager_relationships = {}

    default_eager_relationships = {
        'connection_groups': {
            'eager_relationships': {
                'connections': {
                    'eager_relationships': {
                        'next_step': {}
                    }
                },
                'request': {
                },
            }
        },
        'message': {
            'eager_relationships': {
                        'sender': {},
                        'recipient': {},
                        'widget': {},
                        'attachments': {},
                }
        },
        "template_instance": {}

    }

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, name={self.name!r})"

    def __repr__(self):
        return str(self)
