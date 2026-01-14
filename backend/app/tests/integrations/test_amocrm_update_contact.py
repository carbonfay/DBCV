"""Tests for AmoCRM Update Contact integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.amocrm.update_contact import AmoCrmUpdateContactIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return AmoCrmUpdateContactIntegration()


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
async def test_update_success(integration, credentials_resolver, logger, bot_id):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"_embedded": {"contacts": [{"id": 12345, "name": "John Updated"}]}})

    class AsyncClientMock:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def patch(self, *args, **kwargs):
            # Assert that the request targets the single-contact endpoint
            assert args and args[0].endswith("/api/v4/contacts/12345"), f"Unexpected URL: {args[0] if args else None}"
            # Assert JSON payload is an object (not an array) and contains updated fields
            assert isinstance(kwargs.get("json"), dict), "Expected JSON body to be an object for single-contact update"
            assert kwargs.get("json").get("name") == "John Updated"
            return mock_response

    with patch('app.integrations.amocrm.update_contact.httpx.AsyncClient', return_value=AsyncClientMock()):
        result = await integration.execute(
            config={"subdomain": "mycompany", "id": 12345, "name": "John Updated"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == 12345

@pytest.mark.skip(reason="Требует PostgreSQL initdb, которого нет на Windows")
@pytest.mark.asyncio
async def test_update_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"subdomain": "mycompany", "id": 12345, "name": "John Updated"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401

@pytest.mark.skip(reason="Требует PostgreSQL initdb, которого нет на Windows")
@pytest.mark.asyncio
async def test_update_missing_params(integration, credentials_resolver, logger, bot_id):
    # missing name/custom_fields
    result = await integration.execute(
        config={"subdomain": "mycompany", "id": 12345},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
