from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Text, JSON, Boolean, DateTime, ARRAY, CheckConstraint,
    ForeignKey, func, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import BaseModel


class CredentialEntity(BaseModel):
    __tablename__ = "credentials_entity"
    __table_args__ = (
        Index("ix_cred_bot", "bot_id"),
        Index("ix_cred_provider", "provider"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # зашифрованный blob (JSON-строка с iv/ct), см. secret_box
    data: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)  # "google" | "amocrm" | "yandex_cloud" | ...
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)  # "service_account" | "oauth" | ...
    scopes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    bot_id: Mapped[UUID] = mapped_column(ForeignKey("bot.id"), nullable=False)
    bot: Mapped["BotModel"] = relationship(
        "BotModel",
        back_populates="credentials",
        foreign_keys=bot_id,
        lazy="select",
        load_on_pending=True,
    )