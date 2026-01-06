import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID

if TYPE_CHECKING:
    from .user import UserModel
    from .message import MessageModel


class WidgetModel(BaseModel):
    __tablename__ = "widget"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str]
    description: Mapped[str]
    body: Mapped[str]
    css: Mapped[str]
    js: Mapped[str]
    
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("user.id"), nullable=True, type_=UUID)
    owner: Mapped[Optional["UserModel"]] = relationship("UserModel", foreign_keys=[owner_id], lazy="select", overlaps="widgets")
    
    is_render: Mapped[bool] = mapped_column(default=False, server_default="FALSE", comment="False = шаблон, True = готовый виджет")
    parent_widget_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("widget.id"), nullable=True, type_=UUID)
    parent_widget: Mapped[Optional["WidgetModel"]] = relationship("WidgetModel", foreign_keys=[parent_widget_id], remote_side=[id], lazy="select")

    messages: Mapped[List["MessageModel"]] = relationship("MessageModel", foreign_keys="[MessageModel.widget_id]", back_populates="widget", lazy="select", load_on_pending=True)

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, name={self.name!r})"

    def __repr__(self):
        return str(self)

    default_eager_relationships = {
        "owner": {},
    }