"""Tests for Bitrix24 Get Contact integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.bitrix24.get_contact import Bitrix24GetContactIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return Bitrix24GetContactIntegration()


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(integration):
    md = integration.metadata
    assert md.id == "bitrix24_get_contact"
    assert md.version == "1.0.0"
    assert md.name == "Bitrix24 Get Contact"
    assert md.category == "crm"


@pytest.mark.asyncio
async def test_execute_webhook_success(integration, logger, bot_id):
    creds = {"payload": {"webhook_url": "https://example.bitrix24.ru/rest/1/abc"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"result": {"ID": 123, "NAME": "Ivan"}})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.integrations.bitrix24.get_contact.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"id": 123},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["ID"] == 123


@pytest.mark.asyncio
async def test_execute_domain_token_success(integration, logger, bot_id):
    creds = {"payload": {"domain": "example.bitrix24.ru", "access_token": "token123"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"result": {"ID": 456, "NAME": "Petr"}})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.integrations.bitrix24.get_contact.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"id": 456},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["ID"] == 456


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"id": 1},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_id(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"webhook_url": "https://x"}})

    result = await integration.execute(
        config={},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
