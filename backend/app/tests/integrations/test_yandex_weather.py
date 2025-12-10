"""Тесты для Yandex Weather Get Forecast интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.yandex_weather_get_forecast.get_forecast import (
    YandexWeatherGetForecastIntegration,
)
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return YandexWeatherGetForecastIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"api_key": "test-key"}})
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(integration):
    metadata = integration.metadata

    assert metadata.id == "yandex_weather_get_forecast"
    assert metadata.version == "1.0.0"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "yandex_weather"
    assert metadata.credentials_strategy == "api_key"
    assert "latitude" in metadata.config_schema["properties"]


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "now": 1600000000,
        "now_dt": "2020-09-13T12:00:00Z",
        "forecasts": [{"date": "2020-09-13", "parts": []}],
        "info": {"lat": 55.75, "lon": 37.62, "url": "https://weather.yandex.ru/"},
    }

    async_mock_client = MagicMock()
    async_mock_client.get = AsyncMock(return_value=mock_response)

    # Patch the AsyncClient context manager used in the integration
    with patch("app.integrations.yandex_weather_get_forecast.get_forecast.httpx.AsyncClient") as mock_client_class:
        mock_client_instance = mock_client_class.return_value
        # Ensure __aenter__ returns our mock client instance
        mock_client_instance.__aenter__.return_value = async_mock_client
        mock_client_instance.__aenter__ = AsyncMock(return_value=async_mock_client)

        result = await integration.execute(
            config={"latitude": 55.75, "longitude": 37.62},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert "result" in result["response"]
    assert result["response"]["result"]["info"]["lat"] == 55.75


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"latitude": 55.75, "longitude": 37.62},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_timeout(integration, credentials_resolver, logger, bot_id):
    async_mock_client = MagicMock()
    async_mock_client.get = AsyncMock(side_effect=Exception("timeout"))

    with patch("app.integrations.yandex_weather_get_forecast.get_forecast.httpx.AsyncClient") as mock_client_class:
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.__aenter__.return_value = async_mock_client
        mock_client_instance.__aenter__ = AsyncMock(return_value=async_mock_client)

        result = await integration.execute(
            config={"latitude": 55.75, "longitude": 37.62},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
