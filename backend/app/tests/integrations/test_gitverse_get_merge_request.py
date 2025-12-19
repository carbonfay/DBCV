"""Тесты для Gitverse Get Merge Request интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.gitverse.get_merge_request import GitverseGetMergeRequestIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return GitverseGetMergeRequestIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"api_key": "ghp_testtoken"})
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(integration):
    md = integration.metadata
    assert md.id == "gitverse_get_merge_request"
    assert md.version == "1.0.0"
    assert md.credentials_provider == "gitverse"
    assert md.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    # Мокаем PyGithub объекты
    mock_pr = MagicMock()
    mock_pr.id = 101
    mock_pr.number = 123
    mock_pr.title = "Test PR"
    mock_pr.body = "PR body"
    mock_pr.state = "open"
    mock_pr.merged = False
    mock_pr.merged_at = None
    mock_pr.user = MagicMock()
    mock_pr.user.login = "contributor"
    mock_pr.created_at = None
    mock_pr.updated_at = None
    mock_pr.labels = []

    mock_repo = MagicMock()
    mock_repo.get_pull = MagicMock(return_value=mock_pr)

    mock_gh = MagicMock()
    mock_gh.get_repo = MagicMock(return_value=mock_repo)

    with patch("app.integrations.gitverse.get_merge_request.Github", return_value=mock_gh) as mock_gh_class:
        result = await integration.execute(
            config={"repo_name": "owner/repo", "pull_number": 123},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        res = result["response"]["result"]
        assert res["number"] == 123
        assert res["title"] == "Test PR"

        mock_gh_class.assert_called_once()
        mock_gh.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_pull.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"repo_name": "owner/repo", "pull_number": 1},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_execute_api_error(integration, credentials_resolver, logger, bot_id):
    # Мокаем GithubException
    with patch("app.integrations.gitverse.get_merge_request.Github", side_effect=Exception("API failure")):
        result = await integration.execute(
            config={"repo_name": "owner/repo", "pull_number": 1},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
