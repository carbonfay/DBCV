"""Tests for Bitrix24 Update Deal integration."""
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.integrations.bitrix24.update_deal import Bitrix24UpdateDealIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return Bitrix24UpdateDealIntegration()


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(integration):
    md = integration.metadata
    assert md.id == "bitrix24_update_deal"
    assert md.version == "1.0.0"
    assert md.name == "Bitrix24 Update Deal"
    assert md.category == "crm"


@pytest.mark.asyncio
async def test_execute_webhook_success(integration, logger, bot_id):
    creds = {"payload": {"webhook_url": "https://example.bitrix24.ru/rest/1/abc"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"result": True})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.integrations.bitrix24.update_deal.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"id": 123, "fields": {"TITLE": "New title"}},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"] is True or result["response"]["result"] == {"result": True}


@pytest.mark.asyncio
async def test_execute_domain_token_api_error(integration, logger, bot_id):
    creds = {"payload": {"domain": "example.bitrix24.ru", "access_token": "token123"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"error": "INVALID_REQUEST", "error_description": "Invalid fields"})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.integrations.bitrix24.update_deal.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"id": 456, "fields": {"TITLE": "X"}},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_http_error(integration, logger, bot_id):
    creds = {"payload": {"webhook_url": "https://example.bitrix24.ru/rest/1/abc"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    # Simulate httpx request error
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("timeout"))

    with patch("app.integrations.bitrix24.update_deal.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"id": 1, "fields": {"TITLE": "A"}},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 503


@pytest.mark.asyncio
async def test_execute_validation_missing_params(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"webhook_url": "https://x"}})

    # Missing id
    res1 = await integration.execute(
        config={"fields": {"TITLE": "X"}},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )
    assert res1["response"]["ok"] is False
    assert res1["response"]["error_code"] == 400

    # Missing fields
    res2 = await integration.execute(
        config={"id": 1},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )
    assert res2["response"]["ok"] is False
    assert res2["response"]["error_code"] == 400
