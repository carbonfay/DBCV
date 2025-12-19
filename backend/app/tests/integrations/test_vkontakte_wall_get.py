"""Tests for Vkontakte Wall Get integration."""
import pytest
import httpx
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.vkontakte.wall_get import VkontakteWallGetIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return VkontakteWallGetIntegration()


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(integration):
    md = integration.metadata
    assert md.id == "vkontakte_wall_get"
    assert md.version == "1.0.0"
    assert md.name == "Vkontakte Wall Get"
    assert md.category == "social"


@pytest.mark.asyncio
async def test_execute_success(integration, logger, bot_id):
    creds = {"payload": {"access_token": "token123"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"response": {"count": 1, "items": [{"id": 1}]}})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.integrations.vkontakte.wall_get.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"count": 1},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert isinstance(result["response"]["result"], dict)


@pytest.mark.asyncio
async def test_execute_vk_api_error(integration, logger, bot_id):
    creds = {"payload": {"access_token": "token123"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"error": {"error_msg": "Invalid token"}})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.integrations.vkontakte.wall_get.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"count": 1},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_http_error(integration, logger, bot_id):
    creds = {"payload": {"access_token": "token123"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("timeout"))

    with patch("app.integrations.vkontakte.wall_get.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"count": 1},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 503


@pytest.mark.asyncio
async def test_execute_invalid_owner_id(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"access_token": "token"}})

    result = await integration.execute(
        config={"owner_id": "not-an-int"},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
