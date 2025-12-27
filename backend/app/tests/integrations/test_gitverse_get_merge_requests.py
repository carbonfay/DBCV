"""Тесты для GitVerse Get Merge Requests интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.gitverse.get_merge_requests import GitVerseGetMergeRequestsIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return GitVerseGetMergeRequestsIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"api_key": "token123"}})
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(integration):
    md = integration.metadata
    assert md.id == "gitverse_get_merge_requests"
    assert md.version == "1.0.0"
    assert md.credentials_provider == "gitverse"


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    with patch('app.integrations.gitverse.get_merge_requests.httpx.AsyncClient') as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"iid": 1}]
        mock_response.text = "ok"

        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await integration.execute(
            config={
                "api_url": "https://api.gitverse.ru",
                "repo": "owner/repo",
                "state": "open",
                "page": 2,
                "per_page": 20
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"][0]["iid"] == 1
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert args[0] == "https://api.gitverse.ru/repos/owner/repo/issues"
        assert kwargs["headers"]["Authorization"] == "Bearer token123"
        assert kwargs["params"]["state"] == "open"
        assert kwargs["params"]["page"] == 2
        assert kwargs["params"]["per_page"] == 20


@pytest.mark.asyncio
async def test_execute_no_credentials(logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(side_effect=[None, None])

    result = await GitVerseGetMergeRequestsIntegration().execute(
        config={"repo": "owner/repo"},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_repo(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_fallback_provider_other(logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(side_effect=[None, {"payload": {"api_key": "othertoken"}}])

    with patch('app.integrations.gitverse.get_merge_requests.httpx.AsyncClient') as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"iid": 99}]
        mock_response.text = "ok"

        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await GitVerseGetMergeRequestsIntegration().execute(
            config={"repo": "owner/repo"},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"][0]["iid"] == 99
        mock_client.get.assert_called_once()
