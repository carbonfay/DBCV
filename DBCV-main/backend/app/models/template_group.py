import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from .base import BaseModel, UUID


class TemplateGroupModel(BaseModel):
    __tablename__ = "template_group"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)

    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    owner: Mapped[Optional["UserModel"]] = relationship(
        "UserModel", back_populates="template_groups", lazy="select"
    )

    templates: Mapped[List["TemplateModel"]] = relationship(
        "TemplateModel",
        back_populates="group",
        lazy="selectin",
        uselist=True
    )