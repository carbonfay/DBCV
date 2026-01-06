import uuid
from typing import Optional, List, Union
from sqlalchemy import ForeignKey, Column, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel, UUID


class TemplateInstanceModel(BaseModel):
    __tablename__ = "template_instance"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("template.id", ondelete="SET NULL"),
        nullable=True
    )
    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    inputs_mapping = Column(JSON, nullable=False)
    outputs_mapping = Column(JSON, nullable=False)
    variables = Column(JSON, nullable=True)
    steps = Column(JSON, nullable=False)
    first_step_id = Column(String, nullable=False)
