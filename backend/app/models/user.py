from typing import Optional, List, Dict, Any

from sqlalchemy import ForeignKey, event, insert, Column, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, UUID
from .subscriber import SubscriberModel

from sqlalchemy.dialects.postgresql import JSON
from app.models.role import RoleType


class UserVariables(BaseModel):
    __tablename__ = "user_variables"
    id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), primary_key=True, type_=UUID)
    user: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[id], lazy="selectin", back_populates="variables")
    data: Mapped[Optional[JSON]] = mapped_column(type_=JSON, server_default="{}")

    def get_data(self):
        if self.data is None:
            return self.user.get_data()
        data = self.data if self.data is not None else {}
        return {**self.user.get_data(), **data}


class UserModel(SubscriberModel):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(ForeignKey('subscriber.id'), primary_key=True, type_=UUID)

    username: Mapped[str] = mapped_column(index=True, unique=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    first_name: Mapped[Optional[str]]
    last_name: Mapped[Optional[str]]
    hashed_password: Mapped[str]

    is_active: Mapped[bool] = mapped_column(server_default="true")

    role: Mapped[str] = mapped_column(Enum(RoleType), server_default=RoleType.USER.name, nullable=False)

    bots: Mapped[List["BotModel"]] = relationship("BotModel", back_populates="owner", foreign_keys="[BotModel.owner_id]", lazy='select', uselist=True)

    templates: Mapped[List["TemplateModel"]] = relationship("TemplateModel", back_populates="owner", foreign_keys="[TemplateModel.owner_id]", lazy='select', uselist=True)

    template_groups: Mapped[List["TemplateGroupModel"]] = relationship("TemplateGroupModel", back_populates="owner", foreign_keys="[TemplateGroupModel.owner_id]", lazy='select', uselist=True)

    access_bots: Mapped[List["BotModel"]] = relationship("BotModel", secondary="user_bot_access", back_populates="users")

    my_channels: Mapped[List["ChannelModel"]] = relationship("ChannelModel", back_populates="owner", foreign_keys="[ChannelModel.owner_id]", lazy='select', uselist=True)

    widgets: Mapped[List["WidgetModel"]] = relationship("WidgetModel", foreign_keys="[WidgetModel.owner_id]", lazy='select', uselist=True)

    variables: Mapped[UserVariables] = relationship("UserVariables", lazy="select", cascade="all,delete", foreign_keys="[UserVariables.id]")

    full_eager_relationships = {
        'channels': {},
        'my_channels': {},
        'bots': {
            'eager_relationships': {
                'variables': {}
            }
        },
    }
    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }
    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, username={self.username!r})"

    def __repr__(self):
        return str(self)

    def get_data(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }


@event.listens_for(UserModel, 'after_insert')
def create_bot_variables_on_bot_insert(mapper, connection, instance):
    connection.execute(insert(UserVariables).values(id=instance.id, data={}))