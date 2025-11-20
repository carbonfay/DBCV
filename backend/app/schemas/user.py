from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.decorators import partial_model
from app.schemas.subscriber import SubscriberBase, SubscriberPublic
from app.models.role import RoleType
from app.schemas import register_model_rebuilder

if TYPE_CHECKING:
    from app.schemas.channel import ChannelSimple
    from app.schemas.bot import BotSimple
    from app.schemas.message import MessageSimple


class UserBase(SubscriberBase):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Union[RoleType, str, int] = RoleType.USER
    is_active: bool = True

    @field_validator("role")
    def role_name(cls, role):
        if isinstance(role, str):
            role = RoleType[role]
        elif isinstance(role, int):
            role = RoleType(role)
        return role.name


class UserSimple(UserBase, SubscriberPublic):
    model_config = ConfigDict(from_attributes=True)
    ...


class UserPublic(UserSimple):
    ...


class UserCreate(UserBase):
    password: str


@partial_model
class UserUpdate(UserBase):
    pass


class UserUpdateMe(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str


class UserRegister(BaseModel):
    username: Optional[str] = None
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=5, max_length=50, description="Password, 5 to 50 characters")
    password_check: str = Field(..., min_length=5, max_length=50, description="Password confirmation, 5 to 50 characters")



def _rebuild_models() -> None:
    for model in (
        UserBase,
        UserSimple,
        UserPublic,
        UserCreate,
        UserUpdate,
        UserUpdateMe,
        UpdatePassword,
        UserRegister,
    ):
        model.model_rebuild()


register_model_rebuilder(_rebuild_models)
