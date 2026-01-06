from typing import Optional, List

from sqlalchemy import ForeignKey, event, insert
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, UUID
from .subscriber import SubscriberModel
from sqlalchemy.dialects.postgresql import JSON


class AnonymousUserVariables(BaseModel):
    __tablename__ = "anonymous_user_variables"
    id: Mapped[UUID] = mapped_column(ForeignKey("anonymous_user.id"), primary_key=True, type_=UUID)
    user: Mapped["AnonymousUserModel"] = relationship("AnonymousUserModel", foreign_keys=[id], lazy="selectin",  back_populates="variables")
    data: Mapped[Optional[JSON]] = mapped_column(type_=JSON)

    def get_data(self):
        if self.data is None:
            return self.user.get_data()
        data = self.data if self.data is not None else {}
        return {**self.user.get_data(), **data}


class AnonymousUserModel(SubscriberModel):
    __tablename__ = "anonymous_user"

    id: Mapped[UUID] = mapped_column(ForeignKey('subscriber.id'), primary_key=True, type_=UUID)
    variables: Mapped[AnonymousUserVariables] = relationship("AnonymousUserVariables", lazy="select",  cascade="all,delete", foreign_keys="[AnonymousUserVariables.id]")

    __mapper_args__ = {
        'polymorphic_identity': 'anonymous_user',
    }

    def get_data(self):
        return {
            "id": str(self.id),
        }

    default_eager_relationships = {
        'variables': {},
    }


@event.listens_for(AnonymousUserModel, 'after_insert')
def create_bot_variables_on_bot_insert(mapper, connection, instance):
    connection.execute(insert(AnonymousUserVariables).values(id=instance.id, data={}))