from __future__ import annotations

from typing import Annotated, List, Optional, Dict, Any

from fastapi import APIRouter, Query
from pydantic import BaseModel


router = APIRouter(tags=["credentials-common"])


class ProviderInfo(BaseModel):
    """Информация о провайдере."""
    value: str
    label: str
    description: str
    supported_strategies: List[str]
    payload_examples: Optional[Dict[str, Any]] = None  # Примеры payload для каждой стратегии


class StrategyInfo(BaseModel):
    """Информация о стратегии."""
    value: str
    label: str
    description: str


class ProvidersResponse(BaseModel):
    """Ответ со списком провайдеров."""
    providers: List[ProviderInfo]


class StrategiesResponse(BaseModel):
    """Ответ со списком стратегий."""
    strategies: List[StrategyInfo]


@router.get(
    "/providers",
    response_model=ProvidersResponse,
)
async def get_providers() -> ProvidersResponse:
    """
    Получить список всех доступных провайдеров с поддерживаемыми стратегиями.
    """
    providers = _get_all_providers()
    return ProvidersResponse(providers=providers)


def _get_all_providers() -> List[ProviderInfo]:
    """Вспомогательная функция для получения списка провайдеров."""
    return [
        ProviderInfo(
            value="google",
            label="Google",
            description="Google сервисы (Drive, Sheets, Classroom, OAuth)",
            supported_strategies=["service_account", "oauth"],
            payload_examples={
                "service_account": {
                    "type": "service_account",
                    "project_id": "your-project-id",
                    "private_key_id": "key-id",
                    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
                    "client_email": "service-account@project.iam.gserviceaccount.com",
                    "client_id": "client-id",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                },
                "oauth": {
                    "client_id": "your-client-id",
                    "client_secret": "your-client-secret",
                    "refresh_token": "your-refresh-token",
                    "access_token": "your-access-token"
                }
            }
        ),
        ProviderInfo(
            value="amocrm",
            label="AmoCRM",
            description="CRM система AmoCRM",
            supported_strategies=["oauth"]
        ),
        ProviderInfo(
            value="yandex_cloud",
            label="Yandex Cloud",
            description="Yandex Cloud сервисы",
            supported_strategies=["service_account"]
        ),
        ProviderInfo(
            value="yandex_id",
            label="Yandex ID",
            description="Yandex ID OAuth",
            supported_strategies=["oauth"]
        ),
        ProviderInfo(
            value="telegram",
            label="Telegram",
            description="Telegram Bot API",
            supported_strategies=["api_key"],
            payload_examples={
                "api_key": {
                    "bot_token": "YOUR_BOT_TOKEN_HERE"
                }
            }
        ),
        ProviderInfo(
            value="discord",
            label="Discord",
            description="Discord Bot API",
            supported_strategies=["api_key", "oauth"]
        ),
        ProviderInfo(
            value="openai",
            label="OpenAI",
            description="OpenAI API",
            supported_strategies=["api_key"],
            payload_examples={
                "api_key": {
                    "api_key": "sk-..."
                }
            }
        ),
        ProviderInfo(
            value="other",
            label="Другое",
            description="Другой провайдер",
            supported_strategies=["api_key", "oauth", "basic", "service_account"]
        ),
    ]


@router.get(
    "/strategies",
    response_model=StrategiesResponse,
)
async def get_strategies(
    provider: Annotated[Optional[str], Query(description="Filter by provider")] = None
) -> StrategiesResponse:
    """
    Получить список всех доступных стратегий.
    Если указан provider, возвращает только стратегии, поддерживаемые этим провайдером.
    """
    all_strategies = [
        StrategyInfo(
            value="api_key",
            label="API Key",
            description="Простой API ключ (token, secret key)"
        ),
        StrategyInfo(
            value="oauth",
            label="OAuth 2.0",
            description="OAuth 2.0 авторизация (токены доступа и обновления)"
        ),
        StrategyInfo(
            value="service_account",
            label="Service Account",
            description="Service Account для сервисов Google/Yandex Cloud"
        ),
        StrategyInfo(
            value="basic",
            label="Basic Auth",
            description="HTTP Basic Authentication (username/password)"
        ),
        StrategyInfo(
            value="other",
            label="Другое",
            description="Другая стратегия авторизации"
        ),
    ]
    
    if provider:
        # Получаем информацию о провайдере
        providers = _get_all_providers()
        provider_info = next((p for p in providers if p.value == provider), None)
        if provider_info:
            # Фильтруем стратегии по поддерживаемым провайдером
            strategies = [
                s for s in all_strategies
                if s.value in provider_info.supported_strategies
            ]
            return StrategiesResponse(strategies=strategies)
    
    return StrategiesResponse(strategies=all_strategies)

