"""Tests for OpenWeatherMap integration."""
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.openweathermap.get_current import OpenweathermapGetCurrentIntegration
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return OpenweathermapGetCurrentIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"api_key": "test-api-key"}})
    return resolver


@pytest.fixture
def logger():
    mock_logger = MagicMock(spec=BotLogger)
    mock_logger.error = AsyncMock()
    mock_logger.info = AsyncMock()
    return mock_logger


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_openweathermap_metadata(integration):
    metadata = integration.metadata

    assert metadata.id == "openweathermap_get_current"
    assert metadata.version == "1.0.0"
    assert metadata.name == "OpenWeatherMap Get Current"
    assert metadata.category == "weather"
    assert metadata.credentials_provider == "openweathermap"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_openweathermap_execute_success(integration, credentials_resolver, logger, bot_id):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"name": "London", "main": {"temp": 10}})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = AsyncMock()

    with patch("app.integrations.openweathermap.get_current.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"city": "London", "units": "metric"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["name"] == "London"
    credentials_resolver.get_default_for.assert_awaited_once_with(
        bot_id=bot_id,
        provider="openweathermap",
        strategy="api_key",
    )


@pytest.mark.asyncio
async def test_openweathermap_execute_missing_city(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_openweathermap_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"city": "London"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_openweathermap_execute_missing_api_key(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {}})

    result = await integration.execute(
        config={"city": "London"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
