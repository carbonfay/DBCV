"""Tests for Bitrix24 Update Contact integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.bitrix24.update_contact import Bitrix24UpdateContactIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return Bitrix24UpdateContactIntegration()


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
    assert meta.id == "bitrix24_update_contact"
    assert meta.version == "1.0.0"
    assert meta.name == "Bitrix24 Update Contact"
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
    mock_resp.json = MagicMock(return_value={"result": {"ID": 555}})
    mock_resp.text = "{\"result\": {\"ID\": 555}}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.post = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.update_contact.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"id": 555, "name": "Ivan U", "phone": "+70000000001", "email": "iu@example.com"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["ID"] == 555


@pytest.mark.asyncio
async def test_execute_domain_token_success(integration, credentials_resolver, logger, bot_id):
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"domain": "example.bitrix24.ru", "access_token": "tokabc"}
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"result": {"ID": 666}})
    mock_resp.text = "{\"result\": {\"ID\": 666}}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.post = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.update_contact.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"id": 666, "name": "Petr U", "email": "pu@example.com"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["ID"] == 666


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"id": 1, "name": "NoCred"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_fields(integration, credentials_resolver, logger, bot_id):
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"webhook_url": "https://x/"}})

    # missing id
    res1 = await integration.execute(
        config={"name": "NoId"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )
    assert res1["response"]["ok"] is False
    assert res1["response"]["error_code"] == 400

    # missing name
    res2 = await integration.execute(
        config={"id": 10},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )
    assert res2["response"]["ok"] is False
    assert res2["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_api_error(integration, credentials_resolver, logger, bot_id):
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"webhook_url": "https://x/"}})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"error": "ERR", "error_description": "Bad update"})
    mock_resp.text = "{\"error\": \"ERR\", \"error_description\": \"Bad update\"}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.post = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.update_contact.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"id": 7, "name": "Err"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "Bad update" in result["response"]["description"]
