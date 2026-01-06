from __future__ import annotations
from typing import TYPE_CHECKING
import uuid
from typing import Optional, List, Union
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
import enum
from sqlalchemy import Integer, Enum
from sqlalchemy.dialects.postgresql import JSON
import json

if TYPE_CHECKING:
    from app.models.user import UserModel


class RequestMethodType(enum.Enum):
    get = "get"
    post = "post"
    put = "put"
    delete = "delete"
    patch = "patch"


class RequestModel(BaseModel):
    __tablename__ = "request"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str]
    params: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    content: Mapped[Optional[str]]
    data: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    json_field: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    request_url: Mapped[str]
    method: Mapped[str] = mapped_column(Enum(RequestMethodType), default=RequestMethodType.get)
    attachments: Mapped[Optional[str]]
    headers: Mapped[Optional[str]]
    proxies: Mapped[Optional[str]]

    url_params: Mapped[Optional[JSON]] = mapped_column(type_=JSON)

    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("user.id"), nullable=True)
    owner: Mapped[Optional["UserModel"]] = relationship("UserModel", foreign_keys=[owner_id], lazy="select")

    default_eager_relationships = {
        'owner': {}
    }

    # connection_groups: Mapped[List["ConnectionGroupModel"]] = relationship(back_populates='request', uselist=True, foreign_keys="[ConnectionGroupModel.step_id]", lazy="select")

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, name={self.name!r})"

    def __repr__(self):
        return str(self)
