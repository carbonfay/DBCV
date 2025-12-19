"""Unit tests for GitverseGetCommitsIntegration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.gitverse.get_commits import GitverseGetCommitsIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return GitverseGetCommitsIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"token": "ghp_testtoken"}})
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_metadata(monkeypatch, integration):
    # Ensure library_name is populated when GITHUB_AVAILABLE is True
    monkeypatch.setattr('app.integrations.gitverse.get_commits.GITHUB_AVAILABLE', True)
    metadata = integration.metadata

    assert metadata.id == "gitverse_get_commits"
    assert metadata.version == "1.0.0"
    assert metadata.credentials_provider == "gitverse"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "PyGithub==1.77"


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    # Mock Github and repository commits
    with patch('app.integrations.gitverse.get_commits.Github') as MockGithub:
        mock_gh = MagicMock()
        MockGithub.return_value = mock_gh

        mock_repo = MagicMock()

        # Create a fake commit object similar to PyGithub's structure
        commit_item = MagicMock()
        commit_item.sha = "abc123"
        commit_item.html_url = "https://github.com/owner/repo/commit/abc123"

        commit_obj = MagicMock()
        commit_obj.message = "Test commit"
        author_obj = MagicMock()
        author_obj.name = "Author Name"
        author_obj.date = "2025-01-01T00:00:00Z"
        commit_obj.author = author_obj
        commit_item.commit = commit_obj

        # Provide an author on the top-level (Github user)
        commit_item.author = MagicMock(login="jdoe")

        mock_repo.get_commits.return_value = [commit_item]
        mock_gh.get_repo.return_value = mock_repo

        result = await integration.execute(
            config={"repo_name": "owner/repo"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["count"] == 1
        commits = result["response"]["result"]["commits"]
        assert commits[0]["sha"] == "abc123"
        assert commits[0]["message"] == "Test commit"
        assert commits[0]["author"]["login"] == "jdoe"

        MockGithub.assert_called_once_with(login_or_token="ghp_testtoken")


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"repo_name": "owner/repo"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_execute_library_not_available(monkeypatch, integration, credentials_resolver, logger, bot_id):
    # Simulate missing PyGithub library
    monkeypatch.setattr('app.integrations.gitverse.get_commits.GITHUB_AVAILABLE', False)

    result = await integration.execute(
        config={"repo_name": "owner/repo"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500


@pytest.mark.asyncio
async def test_execute_github_exception(integration, credentials_resolver, logger, bot_id, monkeypatch):
    # Simulate GithubException being raised by the library
    class FakeGithubException(Exception):
        pass

    monkeypatch.setattr('app.integrations.gitverse.get_commits.GithubException', FakeGithubException)

    with patch('app.integrations.gitverse.get_commits.Github') as MockGithub:
        mock_gh = MagicMock()
        MockGithub.return_value = mock_gh
        mock_gh.get_repo.side_effect = FakeGithubException("api error")

        result = await integration.execute(
            config={"repo_name": "owner/repo"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 502
