"""Тесты для OpenWeatherMap UV Index интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.openweathermap.get_uv_index import (
    OpenweathermapGetUvIndexIntegration,
)
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр OpenWeatherMap интеграции."""
    return OpenweathermapGetUvIndexIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(
        return_value={
            "payload": {
                "api_key": "test_api_key",
            }
        }
    )
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_openweathermap_metadata(integration):
    """Тест метаданных интеграции."""
    metadata = integration.metadata

    assert metadata.id == "openweathermap_get_uv_index"
    assert metadata.version == "1.0.0"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx"


@pytest.mark.asyncio
async def test_openweathermap_execute_success(
    integration, credentials_resolver, logger, bot_id
):
    """Тест успешного выполнения интеграции."""
    mock_response_json = {"value": 3.14}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200  # ДОБАВИТЬ!
        mock_resp.headers.get.return_value = "application/json"  # ДОБАВИТЬ!
        mock_resp.json.return_value = mock_response_json
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = await integration.execute(
            config={"lat": 55.7558, "lon": 37.6173},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"] == mock_response_json
        mock_get.assert_awaited_once()


@pytest.mark.asyncio
async def test_openweathermap_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"lat": 55.75, "lon": 37.61},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_openweathermap_execute_missing_config(
    integration, credentials_resolver, logger, bot_id
):
    """Тест выполнения с отсутствующими параметрами lat/lon."""
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_openweathermap_execute_http_error(
    integration, credentials_resolver, logger, bot_id
):
    """Тест обработки HTTPStatusError."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500  # ДОБАВИТЬ!
        mock_resp.headers.get.return_value = "application/json"  # ДОБАВИТЬ!
        mock_resp.raise_for_status.side_effect = Exception("HTTP error")
        mock_get.return_value = mock_resp

        result = await integration.execute(
            config={"lat": 55.75, "lon": 37.61},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500  # Должно быть 500 из блока except


