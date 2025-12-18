"""Tests for Bitrix24 Create Contact integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.bitrix24.create_contact import Bitrix24CreateContactIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return Bitrix24CreateContactIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(integration):
    meta = integration.metadata
    assert meta.id == "bitrix24_create_contact"
    assert meta.version == "1.0.0"
    assert meta.name == "Bitrix24 Create Contact"
    assert meta.category == "crm"
    assert meta.credentials_provider == "other"
    assert meta.credentials_strategy == "oauth"


@pytest.mark.asyncio
async def test_execute_webhook_success(integration, credentials_resolver, logger, bot_id):
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"webhook_url": "https://example.bitrix24.ru/rest/USER/WEBHOOK/"}
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"result": {"ID": 321}})
    mock_resp.text = "{\"result\": {\"ID\": 321}}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.post = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.create_contact.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"name": "Ivan", "phone": "+70000000000", "email": "ivan@example.com"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["ID"] == 321


@pytest.mark.asyncio
async def test_execute_domain_token_success(integration, credentials_resolver, logger, bot_id):
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"domain": "example.bitrix24.ru", "access_token": "tok123"}
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"result": {"ID": 444}})
    mock_resp.text = "{\"result\": {\"ID\": 444}}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.post = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.create_contact.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"name": "Petr", "email": "petr@example.com"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["ID"] == 444


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"name": "NoCred"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_name(integration, credentials_resolver, logger, bot_id):
    # credentials exist but missing required config.name
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"webhook_url": "https://x/"}})

    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_api_error(integration, credentials_resolver, logger, bot_id):
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"webhook_url": "https://x/"}})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"error": "ERROR_CODE", "error_description": "Bad data"})
    mock_resp.text = "{\"error\": \"ERROR_CODE\", \"error_description\": \"Bad data\"}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.post = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.create_contact.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"name": "Err"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "Bad data" in result["response"]["description"]
