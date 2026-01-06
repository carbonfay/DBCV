from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class Provider(str, Enum):
    google = "google"
    amocrm = "amocrm"
    yandex_cloud = "yandex_cloud"
    yandex_id = "yandex_id"
    telegram = "telegram"
    discord = "discord"
    openai = "openai"
    other = "other"


class Strategy(str, Enum):
    service_account = "service_account"
    oauth = "oauth"
    api_key = "api_key"
    basic = "basic"
    other = "other"


# Базовая часть, общая для create/update/out (без payload)
class CredentialBase(BaseModel):
    model_config = ConfigDict(from_attributes=True) 

    name: str = Field(..., max_length=255)
    provider: Provider
    strategy: Strategy
    scopes: Optional[List[str]] = None
    is_default: bool = False

    @field_validator("scopes")
    @classmethod
    def _compact_scopes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if not v:
            return None
        cleaned = [s.strip() for s in v if isinstance(s, str) and s.strip()]
        return cleaned or None


class CredentialCreate(CredentialBase):
    bot_id: UUID
    payload: Dict[str, Any] = Field(..., description="Дешифрованный JSON с секретами (будет зашифрован в БД)")


class CredentialUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    scopes: Optional[List[str]] = None
    is_default: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = None

    @field_validator("scopes")
    @classmethod
    def _compact_scopes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if not v:
            return None
        cleaned = [s.strip() for s in v if isinstance(s, str) and s.strip()]
        return cleaned or None


# Публичное представление (для API/админки): payload не выдаём
class CredentialPublic(CredentialBase):
    id: UUID
    bot_id: UUID
    created_at: datetime
    updated_at: datetime


# Внутреннее представление (для bot_processor/AuthService): с расшифрованным payload
class CredentialInternal(CredentialPublic):
    payload: Dict[str, Any]


# Списочные элементы
class CredentialListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bot_id: UUID
    name: str
    provider: Provider
    strategy: Strategy
    scopes: Optional[List[str]] = None
    is_default: bool = False
    updated_at: datetime


# Ответы API
class CredentialCreateOut(CredentialPublic):
    pass


class CredentialUpdateOut(CredentialPublic):
    pass


class CredentialListOut(BaseModel):
    items: List[CredentialListItem] = Field(default_factory=list)


# Управление дефолтом через отдельный вызов
class CredentialMakeDefaultIn(BaseModel):
    is_default: bool = True


# Контекст выбора/применения авторизации для запроса.
# Используется на стыке api -> handler/AuthService; не хранится в БД.
class AuthSelection(BaseModel):
    bot_id: UUID
    request_url: str
    credentials_id: Optional[UUID] = None     # явный override, если нужно конкретную запись
    strategy_hint: Optional[Strategy] = None   # если у провайдера несколько стратегий
    provider_hint: Optional[Provider] = None
    profile: str = "default"
    hints: Dict[str, Any] = Field(default_factory=dict)