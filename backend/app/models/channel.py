import uuid
from typing import Optional, List
from uuid import uuid4, UUID
from sqlalchemy import ForeignKey, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from .subscriber import subscribers_table
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.event import listen

from sqlalchemy.engine.base import Connection
from sqlalchemy import insert, select
from sqlalchemy.engine.cursor import CursorResult


class ChannelVariables(BaseModel):
    __tablename__ = "channel_variables"
    id: Mapped[UUID] = mapped_column(ForeignKey("channel.id"), primary_key=True, type_=UUID)
    channel: Mapped["ChannelModel"] = relationship("ChannelModel", foreign_keys=[id], lazy="selectin",  back_populates="variables")
    data: Mapped[Optional[JSON]] = mapped_column(type_=JSON, server_default="{}")

    def get_data(self):
        if self.data is None:
            return self.channel.get_data()
        data = self.data if self.data is not None else {}
        return {**self.channel.get_data(), **data}


class ChannelModel(BaseModel):
    __tablename__ = "channel"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)
    is_public: Mapped[bool] = mapped_column(default=False)

    owner_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    owner: Mapped[Optional["UserModel"]] = relationship("UserModel", back_populates="my_channels", foreign_keys=owner_id,  lazy="select", load_on_pending=True)
    default_bot_id: Mapped[UUID | None] = mapped_column(ForeignKey("bot.id"), nullable=True)
    default_bot: Mapped[Optional["BotModel"]] = relationship("BotModel", foreign_keys=default_bot_id,  lazy="selectin", load_on_pending=True)
    subscribers: Mapped[List["SubscriberModel"]] = relationship(secondary=subscribers_table, back_populates="channels", uselist=True, lazy="select", load_on_pending=True)

    messages: Mapped[List["MessageModel"]] = relationship("MessageModel", back_populates="channel", lazy="select",  uselist=True, order_by="MessageModel.created_at")

    variables: Mapped[ChannelVariables] = relationship("ChannelVariables", lazy="select",  cascade="all,delete", foreign_keys="[ChannelVariables.id]")

    sessions: Mapped[List["SessionModel"]] = relationship("SessionModel", back_populates="channel", lazy="select",  uselist=True, cascade="all,delete")
    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, name={self.name!r})"

    def __repr__(self):
        return str(self)

    def get_data(self):
        return {
            "id": str(self.id),
            "name": self.name,
        }

    default_eager_relationships = {
        'default_bot': {
            'eager_relationships': {
                'variables': {},
                }
        },
        'variables': {},
        'owner': {},
        'subscribers': {}
    }

    simple_eager_relationships = None

    full_eager_relationships = {
        'default_bot': {
            'eager_relationships': {
                'variables': {},
                }
        },
        'variables': {},
        'owner': {},
        'subscribers': {},
        'messages': {
            'eager_relationships': {
                'widget': {}
            }
        }
    }


@event.listens_for(ChannelModel, 'after_insert')
def create_channel_variables_on_channel_insert(mapper, connection: Connection, channel: ChannelModel):
    connection.execute(insert(ChannelVariables).values(id=channel.id, data={}))

