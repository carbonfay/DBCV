"""Tests for Bitrix24 Create Task integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.bitrix24.create_task import Bitrix24CreateTaskIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return Bitrix24CreateTaskIntegration()


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.mark.asyncio
async def test_metadata(integration):
    md = integration.metadata
    assert md.id == "bitrix24_create_task"
    assert md.version == "1.0.0"
    assert md.name == "Bitrix24 Create Task"
    assert md.category == "tasks"


@pytest.mark.asyncio
async def test_execute_webhook_success(integration, logger, bot_id):
    # credentials with webhook
    creds = {"payload": {"webhook_url": "https://example.bitrix24.ru/rest/1/abc"}}

    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    # mock httpx.AsyncClient and response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"result": {"task": {"id": 101}}})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.integrations.bitrix24.create_task.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"title": "Test task", "description": "desc", "responsible_id": 1},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["task"]["id"] == 101


@pytest.mark.asyncio
async def test_execute_domain_token_success(integration, logger, bot_id):
    creds = {"payload": {"domain": "example.bitrix24.ru", "access_token": "token123"}}
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=creds)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"result": {"task": {"id": 202}}})

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.integrations.bitrix24.create_task.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={"title": "Domain task"},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["result"]["task"]["id"] == 202


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"title": "Test"},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_title_and_fields(integration, logger, bot_id):
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
