from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.decorators import partial_model


class SubscriberBase(BaseModel):
    type: str = "user"
    pass


class SubscriberPublic(SubscriberBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | str
