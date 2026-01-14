"""Tests for AmoCRM Create Contact integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.amocrm.create_contact import AmoCrmCreateContactIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

pytestmark = pytest.mark.filterwarnings("ignore:.*requested an async fixture.*")

@pytest.fixture
def integration():
    return AmoCrmCreateContactIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "base_domain": "mycompany.amocrm.ru",
            "access_token": "access123",
            "refresh_token": "refresh123",
            "client_id": "cid",
            "client_secret": "csecret",
        }
    })
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")

@pytest.mark.skip(reason="Требует PostgreSQL initdb, которого нет на Windows")
@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    # Mock httpx AsyncClient
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"_embedded": {"contacts": [{"id": 12345, "name": "John"}]}})

    class AsyncClientMock:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return mock_response

    with patch('app.integrations.amocrm.create_contact.httpx.AsyncClient', return_value=AsyncClientMock()):
        result = await integration.execute(
            config={"subdomain": "mycompany", "name": "John"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == 12345

@pytest.mark.skip(reason="Требует PostgreSQL initdb, которого нет на Windows")
@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"subdomain": "mycompany", "name": "John"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401

@pytest.mark.skip(reason="Требует PostgreSQL initdb, которого нет на Windows")
@pytest.mark.asyncio
async def test_execute_missing_params(integration, credentials_resolver, logger, bot_id):
    # missing name
    result = await integration.execute(
        config={"subdomain": "mycompany"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
