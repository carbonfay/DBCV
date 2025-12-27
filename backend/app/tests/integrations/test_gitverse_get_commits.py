"""Тесты для GitVerse Get Commits интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.gitverse.get_commits import GitVerseGetCommitsIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return GitVerseGetCommitsIntegration()


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
    assert md.id == "gitverse_get_commits"
    assert md.version == "1.0.0"
    assert md.credentials_provider == "gitverse"


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    with patch('app.integrations.gitverse.get_commits.httpx.AsyncClient') as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"sha": "abc123"}]
        mock_response.text = "ok"

        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await integration.execute(
            config={
                "repo": "owner/repo",
                "sha": "main",
                "page": 1,
                "per_page": 5
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"][0]["sha"] == "abc123"
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert args[0] == "https://api.gitverse.ru/repos/owner/repo/commits"
        assert kwargs["headers"]["Authorization"] == "Bearer token123"
        assert kwargs["params"]["sha"] == "main"
        assert kwargs["params"]["page"] == 1
        assert kwargs["params"]["per_page"] == 5


@pytest.mark.asyncio
async def test_execute_no_credentials(logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(side_effect=[None, None])

    result = await GitVerseGetCommitsIntegration().execute(
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

    with patch('app.integrations.gitverse.get_commits.httpx.AsyncClient') as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"sha": "fallback"}]
        mock_response.text = "ok"

        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await GitVerseGetCommitsIntegration().execute(
            config={"repo": "owner/repo"},
            credentials_resolver=resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"][0]["sha"] == "fallback"
        mock_client.get.assert_called_once()
