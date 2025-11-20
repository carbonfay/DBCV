import uuid
from typing import Optional, List, Union, Dict, Any
from sqlalchemy import ForeignKey, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from sqlalchemy.types import JSON


class MessageModel(BaseModel):
    __tablename__ = "message"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    text: Mapped[str | None]
    params: Mapped[Optional[JSON] | None] = mapped_column(type_=JSON)

    channel_id: Mapped[UUID | None] = mapped_column(ForeignKey("channel.id"), nullable=True)
    channel: Mapped[Optional["ChannelModel"] | None] = relationship("ChannelModel", back_populates="messages", foreign_keys=channel_id, lazy="select")

    recipient_id: Mapped[UUID | None] = mapped_column(ForeignKey("subscriber.id"), nullable=True)
    recipient: Mapped["SubscriberModel"] = relationship("SubscriberModel", back_populates="recipient_messages", foreign_keys=recipient_id, lazy="select")

    sender_id: Mapped[UUID | None] = mapped_column(ForeignKey("subscriber.id"), nullable=True)
    sender: Mapped[Optional["SubscriberModel"] | None] = relationship("SubscriberModel", back_populates="sender_messages", foreign_keys=sender_id, lazy="select")

    step_id: Mapped[UUID | None] = mapped_column(ForeignKey("step.id"), nullable=True)
    step: Mapped["StepModel"] = relationship("StepModel", back_populates='message', foreign_keys=step_id, lazy="select")

    widget_id: Mapped[UUID | None] = mapped_column(ForeignKey("widget.id"), nullable=True)
    widget: Mapped["WidgetModel"] = relationship("WidgetModel", foreign_keys=widget_id, back_populates="messages", lazy="selectin")

    attachments: Mapped[List["AttachmentModel"]] = relationship("AttachmentModel", foreign_keys="[AttachmentModel.message_id]", back_populates="message", lazy="selectin")

    emitter: Mapped[Optional["EmitterModel"]] = relationship("EmitterModel", foreign_keys="[EmitterModel.message_id]", back_populates="message", lazy="select")

    default_eager_relationships = {
        'sender': {},
        'recipient': {},
        'widget': {},
        'attachments': {},
        'emitter': {}
    }

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, text={self.text!r})"

    def __repr__(self):
        return str(self)

    @classmethod
    async def get_messages_by_channel(cls, session: AsyncSession, channel_id: UUID,
                                      skip: int = 0,
                                      limit: int | None = None,
                                      eager_relationships: Optional[Dict[str, Any]] = None,
                                      fields: Optional[List[str]] = None) -> List[Optional['MessageModel']]:
        return await cls.get_all(session, skip=skip, limit=limit, eager_relationships=eager_relationships,
                                 fields=fields, order_by=desc(cls.created_at), channel_id=channel_id)

    def get_data(self):

        return {
            "id": str(self.id) if self.id is not None else None,
            "text": self.text,
            "params": self.params,
            "sender_id": str(self.sender_id) if self.sender_id is not None else None,
            "recipient_id": str(self.recipient_id)if self.recipient_id is not None else None,
            "channel_id": str(self.channel_id)if self.channel_id is not None else None,
            'attachments': [attachment.get_dict() for attachment in self.attachments],
            "created_at": str(self.created_at)
        }

    def get_dict(self):
        return {"message": {
            "id": str(self.id) if self.id is not None else None,
            "text": self.text,
            "params": self.params,
            "sender_id": str(self.sender_id) if self.sender_id is not None else None,
            "recipient_id": str(self.recipient_id)if self.recipient_id is not None else None,
            "channel_id": str(self.channel_id)if self.channel_id is not None else None,
            'attachments': [attachment.get_dict() for attachment in self.attachments]
        }}

