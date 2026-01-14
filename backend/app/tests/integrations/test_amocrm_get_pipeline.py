"""Tests for AmoCRM Get Pipeline integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.amocrm.get_pipeline import AmoCrmGetPipelineIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return AmoCrmGetPipelineIntegration()


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
async def test_list_pipelines_success(integration, credentials_resolver, logger, bot_id):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"_embedded": {"pipelines": [{"id": 1, "name": "Main"}]}})

    class AsyncClientMock:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            return mock_response

    with patch('app.integrations.amocrm.get_pipeline.httpx.AsyncClient', return_value=AsyncClientMock()):
        result = await integration.execute(
            config={"subdomain": "mycompany"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert isinstance(result["response"]["result"], dict)

@pytest.mark.skip(reason="Требует PostgreSQL initdb, которого нет на Windows")
@pytest.mark.asyncio
async def test_get_pipeline_by_id_success(integration, credentials_resolver, logger, bot_id):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"id": 123, "name": "Main"})

    class AsyncClientMock:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            return mock_response

    with patch('app.integrations.amocrm.get_pipeline.httpx.AsyncClient', return_value=AsyncClientMock()):
        result = await integration.execute(
            config={"subdomain": "mycompany", "pipeline_id": 123},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == 123

@pytest.mark.skip(reason="Требует PostgreSQL initdb, которого нет на Windows")
@pytest.mark.asyncio
async def test_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"subdomain": "mycompany"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
