import uuid
from typing import Optional, List, Union
from sqlalchemy import ForeignKey, Column, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from app.models.block import Block


class TemplateModel(BaseModel):
    __tablename__ = "template"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    inputs = Column(JSON, nullable=False)
    outputs = Column(JSON, nullable=False)
    variables = Column(JSON, nullable=True)
    steps = Column(JSON, nullable=False)
    first_step_id = Column(String, nullable=False)

    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    owner: Mapped["UserModel"] = relationship("UserModel", back_populates="templates", foreign_keys=owner_id,
                                              lazy="select")

    group_id: Mapped[UUID | None] = mapped_column(ForeignKey("template_group.id", ondelete="SET NULL"), nullable=True)
    group: Mapped[Optional["TemplateGroupModel"]] = relationship("TemplateGroupModel", back_populates="templates", lazy="select")

    bot_id: Mapped[UUID | None] = mapped_column(ForeignKey("bot.id", ondelete="SET NULL"), nullable=True)

    default_eager_relationships = {
        'group': {
            'eager_relationships': {
                'owner': {}
            }
        },
        'owner': {}
    }