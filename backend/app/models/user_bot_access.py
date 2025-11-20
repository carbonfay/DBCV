from sqlalchemy import Column, ForeignKey, Enum, Table
from .base import BaseModel, UUID
from app.models.access import AccessType

user_bot_access = Table(
    "user_bot_access", BaseModel.metadata,
    Column("user_id", UUID, ForeignKey("user.id"), primary_key=True),
    Column("bot_id", UUID, ForeignKey("bot.id"), primary_key=True),
    Column("access_type", Enum(AccessType), nullable=False, default=AccessType.NO_ACCESS,
           server_default=AccessType.NO_ACCESS.name)
)