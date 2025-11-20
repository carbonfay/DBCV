import uuid
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, UUID
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import ForeignKey
from sqlalchemy import Integer


subscribers_table = Table(
    "subscribers_table",
    BaseModel.metadata,
    Column("subscriber_id", ForeignKey("subscriber.id"), primary_key=True),
    Column("channel_id", ForeignKey("channel.id"), primary_key=True),

)


class SubscriberModel(BaseModel):
    __tablename__ = "subscriber"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    channels: Mapped[List["ChannelModel"]] = relationship(secondary=subscribers_table, back_populates="subscribers", lazy="select", load_on_pending=True, uselist=True)
    type: Mapped[str] = mapped_column(nullable=True, default='subscriber')

    __mapper_args__ = {
        "with_polymorphic": "*",
        'polymorphic_on': "type",
        'polymorphic_identity': 'subscriber',
    }

    recipient_messages: Mapped[List["MessageModel"]] = relationship("MessageModel", back_populates="recipient", uselist=True, foreign_keys="[MessageModel.recipient_id]", lazy="select", load_on_pending=True)
    sender_messages: Mapped[List["MessageModel"]] = relationship("MessageModel", back_populates="sender", uselist=True, foreign_keys="[MessageModel.sender_id]", order_by="MessageModel.created_at", lazy="select", load_on_pending=True)
    sessions: Mapped[List["SessionModel"]] = relationship("SessionModel", back_populates="user", lazy="select",  uselist=True, cascade="all,delete")

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, type={self.type!r})"

    def __repr__(self):
        return str(self)

    def is_bot(self):
        return self.type == "bot"

    def is_user(self):
        return self.type == "user"

    def is_anonymous_user(self):
        return self.type == "anonymous_user"

    def is_any_user(self):
        return self.is_user() or self.is_anonymous_user()



