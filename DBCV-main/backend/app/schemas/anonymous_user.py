from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.utils.decorators import partial_model
from app.schemas.subscriber import SubscriberBase, SubscriberPublic


class AnonymousUserBase(SubscriberBase):
    ...


class AnonymousUserSimple(AnonymousUserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | str


