from typing import Optional, List, Union

from sqlalchemy import ForeignKey, insert
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from .subscriber import SubscriberModel
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import event


class BotVariables(BaseModel):
    __tablename__ = "bot_variables"
    id: Mapped[UUID] = mapped_column(ForeignKey("bot.id"), primary_key=True, type_=UUID)
    bot: Mapped["BotModel"] = relationship("BotModel", foreign_keys=[id], lazy="selectin",  back_populates="variables")
    data: Mapped[Optional[JSON]] = mapped_column(type_=JSON, server_default="{}")

    def get_data(self):
        if self.data is None:
            return self.bot.get_data()
        data = self.data if self.data is not None else {}
        return {**self.bot.get_data(), **data}


class BotModel(SubscriberModel):
    __tablename__ = "bot"

    id: Mapped[UUID] = mapped_column(ForeignKey('subscriber.id'), primary_key=True, type_=UUID)

    name: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(default=None, nullable=True)

    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    owner: Mapped["UserModel"] = relationship("UserModel", back_populates="bots", foreign_keys=owner_id, lazy="select")

    first_step_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('step.id'), nullable=True)
    first_step: Mapped[Optional["StepModel"]] = relationship("StepModel", foreign_keys=first_step_id, lazy="selectin")

    sessions: Mapped[List["SessionModel"]] = relationship("SessionModel", back_populates="bot", foreign_keys="[SessionModel.bot_id]", lazy="select", uselist=True, cascade="all,delete")

    steps: Mapped[List["StepModel"]] = relationship("StepModel", back_populates="bot", foreign_keys="[StepModel.bot_id]", lazy="select", uselist=True, cascade="all,delete")

    variables: Mapped[BotVariables] = relationship("BotVariables", lazy="select", cascade="all,delete", foreign_keys="[BotVariables.id]")

    master_connection_groups: Mapped[List["ConnectionGroupModel"]] = relationship(
        "ConnectionGroupModel", back_populates="bot", foreign_keys="[ConnectionGroupModel.bot_id]",
        lazy="selectin", uselist=True, cascade="all,delete")

    notes: Mapped[List["NoteModel"]] = relationship("NoteModel", back_populates="bot", foreign_keys="[NoteModel.bot_id]", lazy="select", uselist=True, cascade="all,delete")

    emitters: Mapped[List["EmitterModel"]] = relationship("EmitterModel", back_populates="bot", lazy="select", uselist=True, foreign_keys="[EmitterModel.bot_id]", cascade="all,delete")
    credentials: Mapped[List["CredentialEntity"]] = relationship("CredentialEntity", back_populates="bot", lazy="select", uselist=True, foreign_keys="[CredentialEntity.bot_id]", cascade="all,delete")

    users: Mapped[List["UserModel"]] = relationship("UserModel", back_populates="access_bots", secondary="user_bot_access")

    logs: Mapped[Optional[str]]

    config: Mapped[Optional[JSON]] = mapped_column(type_=JSON, nullable=True)

    cache_structure: Mapped[Optional[JSON]] = mapped_column(type_=JSON, nullable=True)

    list_select_related = ["owner", "first_step", "steps", "variables", "master_connection_groups", "notes", "emitters", "channels"]

    default_eager_relationships = {
        'channels': {},
        'first_step': {
            'eager_relationships': {
                'message': {
                    'sender': {},
                    'recipient': {},
                    'widget': {},
                    'attachments': {},
                }
            },
        },
        'steps': {
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
                                'sender': {},
                                'recipient': {},
                                'widget': {},
                                'attachments': {},
                    }
                }

            }
        },
        'variables': {},
        'master_connection_groups': {
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
        'notes': {},
        'emitters': {
            'eager_relationships': {
                'cron': {},
                'message': {
                    'sender': {},
                    'recipient': {},
                    'widget': {},
                    'attachments': {},
                }
            }
        },
        'owner': {}
    }

    __mapper_args__ = {
        'polymorphic_identity': 'bot',
    }

    def __str__(self):
        return f"{self.__tablename__.capitalize()}"

    def __repr__(self):
        return str(self)

    def get_data(self):
        return {
            "id": str(self.id),
            "name": self.name,
            # "last_message": self.sender_messages[-1].get_data() if self.sender_messages else None,
        }


@event.listens_for(BotModel, 'after_insert')
def create_bot_variables_on_bot_insert(mapper, connection, instance):
    connection.execute(insert(BotVariables).values(id=instance.id, data={}))


