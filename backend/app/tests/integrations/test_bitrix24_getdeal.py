"""Tests for Bitrix24 GetDeal integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.bitrix24.get_deal import Bitrix24GetDealIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return Bitrix24GetDealIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    # default will be overridden in tests where needed
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
    assert meta.id == "bitrix24_getdeal"
    assert meta.version == "1.0.0"
    assert meta.name == "Bitrix24 Get Deal"
    assert meta.category == "crm"
    assert meta.credentials_provider == "bitrix24"
    assert meta.credentials_strategy == "oauth"
    assert meta.library_name == "httpx"


@pytest.mark.asyncio
async def test_execute_webhook_success(integration, credentials_resolver, logger, bot_id):
    # prepare credentials with webhook
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"webhook_url": "https://example.bitrix24.ru/rest/USER/WEBHOOK/"}
    })

    # mock httpx AsyncClient to return a successful response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"ID": 598, "TITLE": "Deal title"})
    mock_resp.text = "{\"ID\": 598, \"TITLE\": \"Deal title\"}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.post = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.get_deal.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"id": 598},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["ID"] == 598


@pytest.mark.asyncio
async def test_execute_domain_token_success(integration, credentials_resolver, logger, bot_id):
    # prepare credentials with domain + access_token
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {"domain": "example.bitrix24.ru", "access_token": "token123"}
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"result": {"ID": 777, "TITLE": "Domain Deal"}})
    mock_resp.text = "{\"result\": {\"ID\": 777}}"
    mock_resp.raise_for_status = MagicMock()

    client_mock = MagicMock()
    client_mock.get = AsyncMock(return_value=mock_resp)

    with patch("app.integrations.bitrix24.get_deal.httpx.AsyncClient") as AsyncClientMock:
        AsyncClientMock.return_value.__aenter__.return_value = client_mock

        result = await integration.execute(
            config={"id": 777},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    # depending on implementation, result may be wrapped; check presence
    assert (result["response"]["result"]["result"]["ID"] == 777) or (result["response"]["result"]["ID"] == 777)


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"id": 1},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_no_endpoint(integration, credentials_resolver, logger, bot_id):
    # credentials present but no webhook or domain
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {}})

    result = await integration.execute(
        config={"id": 999},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
