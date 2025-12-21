"""Тесты для GitVerse Create Issue интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.gitverse.create_issue import GitVerseCreateIssueIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return GitVerseCreateIssueIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    # Возвращаем payload внутри ключа payload для совместимости
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
    assert md.id == "gitverse_create_issue"
    assert md.version == "1.0.0"
    assert md.credentials_provider == "gitverse"


@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    with patch('app.integrations.gitverse.create_issue.httpx.AsyncClient') as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"number": 1, "title": "Test Issue"}
        mock_response.text = "created"

        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await integration.execute(
            config={
                "api_url": "https://api.github.com",
                "repo": "owner/repo",
                "title": "Test Issue",
                "body": "Details"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["number"] == 1
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"api_url": "https://api.github.com", "repo": "owner/repo", "title": "T"},
        credentials_resolver=resolver,
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
async def test_execute_gitlab_success(integration, credentials_resolver, logger, bot_id):
    # Ensure GitLab path and payload mapping work: project_id used, description instead of body, labels comma-separated
    with patch('app.integrations.gitverse.create_issue.httpx.AsyncClient') as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"iid": 42, "title": "GL Issue"}
        mock_response.text = "created"

        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await integration.execute(
            config={
                "api_url": "https://gitlab.example.com",
                "repo": "group/project",
                "project_id": "group/project",
                "api_type": "gitlab",
                "title": "GL Issue",
                "body": "Details",
                "labels": ["a", "b"],
                "assignees": [123]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        # endpoint contains /api/v4/projects/{id}/issues
        assert "/api/v4/projects/" in args[0]
        assert "issues" in args[0]
        # payload mapping checks
        assert kwargs["json"]["title"] == "GL Issue"
        assert kwargs["json"]["description"] == "Details"
        assert kwargs["json"]["labels"] == "a,b"
        assert "assignee_ids" in kwargs["json"]
