import uuid
from typing import Optional, List, Union

from sqlalchemy import ForeignKey, insert, event, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from sqlalchemy.dialects.postgresql import JSON


class SessionVariables(BaseModel):
    __tablename__ = "session_variables"
    id: Mapped[UUID] = mapped_column(ForeignKey("session.id"), primary_key=True, type_=UUID)
    session: Mapped["SessionModel"] = relationship("SessionModel", foreign_keys=[id], lazy="selectin", back_populates="variables")
    data: Mapped[Optional[JSON]] = mapped_column(type_=JSON, server_default="{}")

    def get_data(self):
        if self.data is None:
            return self.session.get_data()
        data = self.data if self.data is not None else {}
        return {**self.session.get_data(), **data}


class SessionModel(BaseModel):
    __tablename__ = "session"
    __table_args__ = (UniqueConstraint('user_id', 'bot_id', 'channel_id'), )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("subscriber.id"), nullable=False)
    user:  Mapped["SubscriberModel"] = relationship("SubscriberModel", foreign_keys=user_id, back_populates="sessions")

    bot_id: Mapped[UUID] = mapped_column(ForeignKey("bot.id"), nullable=False)
    bot: Mapped["BotModel"] = relationship("BotModel", foreign_keys=bot_id, back_populates="sessions")

    channel_id: Mapped[UUID] = mapped_column(ForeignKey("channel.id"), nullable=False)
    channel: Mapped["ChannelModel"] = relationship("ChannelModel", foreign_keys=channel_id, back_populates="sessions")

    step_id: Mapped[UUID] = mapped_column(ForeignKey("step.id"))
    step: Mapped["StepModel"] = relationship("StepModel", foreign_keys=step_id, lazy="selectin")

    variables: Mapped[SessionVariables] = relationship("SessionVariables", lazy="select", cascade="all,delete", foreign_keys="[SessionVariables.id]")

    __table_args__ = (
        Index('ix_session_user_id_bot_id_channel_id', user_id, bot_id, channel_id, unique=True),
    )

    default_eager_relationships = {
        'bot': {
            'first_step': {
                'eager_relationships': {
                    'message': {
                    }
                },
            },
        },
        'step': {
            'eager_relationships': {
                'connection_groups': {
                    'eager_relationships': {
                        'connections': {
                            'eager_relationships': {
                                'next_step': {}
                            }
                        },
                        'request': {
                        }
                    },
                },
                'message': {
                    'eager_relationships': {
                        'widget': {},
                        'attachments': {}
                    }
                }

            }
        },
        'variables': {},
        'user': {
            'variables': {}
        },
        'channel': {
            'default_bot': {
                'first_step': {
                    'eager_relationships': {
                        'message': {
                        }
                    },
                },
            }
        }
    }

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, user_id={self.user_id}, bot_id={self.bot_id}, channel_id={self.channel_id}, step_id={self.step_id})"

    def __repr__(self):
        return str(self)

    def get_data(self):
        return {
            "id": str(self.id),
        }


@event.listens_for(SessionModel, 'after_insert')
def create_bot_variables_on_bot_insert(mapper, connection, instance):
    connection.execute(insert(SessionVariables).values(id=instance.id, data={}))