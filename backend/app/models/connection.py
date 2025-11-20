import uuid
from typing import Optional, List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID

import enum
from sqlalchemy import Integer, Enum
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import JSON


class SearchType(str, enum.Enum):
    response = "response"
    message = "message"
    code = "code"
    integration = "integration"


class ConnectionGroupModel(BaseModel):
    __tablename__ = "connection_group"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    search_type: Mapped[SearchType] = mapped_column(Enum(SearchType), default=SearchType.message)
    priority: Mapped[int] = mapped_column(default=0, server_default="0")
    code: Mapped[Optional[str]]

    request_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("request.id"), nullable=True)
    request: Mapped[Optional["RequestModel"]] = relationship("RequestModel", foreign_keys=request_id, lazy="selectin", cascade="all,delete")

    step_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("step.id"), nullable=True)
    step: Mapped[Optional["StepModel"]] = relationship("StepModel", back_populates="connection_groups", foreign_keys=[step_id], lazy="select")

    connections: Mapped[List["ConnectionModel"]] = relationship("ConnectionModel", foreign_keys="[ConnectionModel.group_id]", back_populates="group", lazy="selectin", cascade="all, delete-orphan")

    bot_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("bot.id"), nullable=True)
    bot: Mapped[Optional["BotModel"]] = relationship("BotModel", back_populates="master_connection_groups", foreign_keys=[bot_id],
                                           lazy="select")

    variables: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    
    # Поля для интеграций
    integration_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    integration_config: Mapped[Optional[JSON]] = mapped_column(type_=JSON, nullable=True)

    default_eager_relationships = {

        'connections': {
            'eager_relationships': {
                'next_step': {}
            }
        },
        'request': {
        }
    }

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, step_name={self.step.name if self.step_id else ''})"

    def __repr__(self):
        return str(self)


class ConnectionModel(BaseModel):
    __tablename__ = "connection"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)

    group_id: Mapped[UUID] = mapped_column(ForeignKey("connection_group.id"))
    group: Mapped[ConnectionGroupModel] = relationship("ConnectionGroupModel", back_populates="connections", foreign_keys=[group_id], lazy="select", load_on_pending=True)

    rules: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    filters: Mapped[Optional[JSON]] = mapped_column(type_=JSON)

    next_step_id: Mapped[UUID] = mapped_column(ForeignKey("step.id"))
    next_step: Mapped["StepModel"] = relationship("StepModel", back_populates="back_connections", foreign_keys=[next_step_id], lazy="select", load_on_pending=True)
    priority: Mapped[int] = mapped_column(default=0, server_default="0")

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id})"

    def __repr__(self):
        return str(self)





