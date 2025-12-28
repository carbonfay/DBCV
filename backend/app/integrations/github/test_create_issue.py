import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.github.create_issue import GitHubCreateIssueIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

from app.integrations.github.token_resolver import (
    GitHubCredentialsNotFoundError,
    GitHubTokenNotFoundError,
)


class DummyIssue:
    def to_dict(self):
        return {"id": 101, "number": 7, "title": "Bug: cannot login"}


class DummyIssueNoToDict(dict):
    pass


class DummyApiException(Exception):
    def __init__(self, status=None, message="api error"):
        super().__init__(message)
        self.status = status


@pytest.fixture
def integration():
    return GitHubCreateIssueIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"token": "t"}})
    return resolver


@pytest.fixture
def logger():
    lg = MagicMock(spec=BotLogger)
    lg.error = AsyncMock()
    return lg


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_github_metadata(integration):
    md = integration.metadata

    assert md.id == "github_create_issue"
    assert md.version == "1.0.0"
    assert md.name == "GitHub Create Issue"
    assert md.category == "storage"
    assert md.credentials_provider == "other"
    assert md.credentials_strategy == "api_key"

    ex = md.examples[0]["config"]
    assert ex["owner_name"] == "octocat"
    assert ex["repository_name"] == "Hello-World"
    assert ex["title"]
    assert ex["labels"] == ["bug", "triage"]



@pytest.mark.asyncio
async def test_execute_success_minimal_payload(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def create_issue(self, *, token, owner, repo, request):
            assert request.body is None
            assert request.assignee is None
            assert request.assignees is None
            assert request.labels is None
            assert request.milestone is None
            assert request.type is None
            return DummyIssue()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.create_issue._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.create_issue.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={
                "owner_name": "octocat",
                "repository_name": "Hello-World",
                "title": "Bug: cannot login",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == 101
    logger.error.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_success_issue_no_to_dict(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def create_issue(self, *, token, owner, repo, request):
            return DummyIssueNoToDict({"k": "v"})

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.create_issue._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.create_issue.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={
                "owner_name": "octocat",
                "repository_name": "Hello-World",
                "title": "Bug: cannot login",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {"k": "v"}
    logger.error.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_token_not_found(integration, credentials_resolver, logger, bot_id):
    async def fake_resolve_token(*, credentials_resolver, bot_id):
        raise GitHubTokenNotFoundError("no token")

    with patch("app.integrations.github.create_issue._resolve_github_token", new=fake_resolve_token):
        result = await integration.execute(
            config={
                "owner_name": "octocat",
                "repository_name": "Hello-World",
                "title": "Bug: cannot login",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "no token" in result["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_execute_credentials_not_found(integration, credentials_resolver, logger, bot_id):
    async def fake_resolve_token(*, credentials_resolver, bot_id):
        raise GitHubCredentialsNotFoundError("no creds")

    with patch("app.integrations.github.create_issue._resolve_github_token", new=fake_resolve_token):
        result = await integration.execute(
            config={
                "owner_name": "octocat",
                "repository_name": "Hello-World",
                "title": "Bug: cannot login",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "no creds" in result["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_execute_api_exception_with_status(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def create_issue(self, *, token, owner, repo, request):
            raise DummyApiException(status=403, message="Forbidden")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.create_issue.ApiException", DummyApiException), \
         patch("app.integrations.github.create_issue._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.create_issue.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={
                "owner_name": "octocat",
                "repository_name": "Hello-World",
                "title": "Bug: cannot login",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 403
    assert "Forbidden" in result["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_execute_api_exception_without_status(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def create_issue(self, *, token, owner, repo, request):
            raise DummyApiException(status=None, message="Boom")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.create_issue.ApiException", DummyApiException), \
         patch("app.integrations.github.create_issue._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.create_issue.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={
                "owner_name": "octocat",
                "repository_name": "Hello-World",
                "title": "Bug: cannot login",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_execute_unexpected_exception(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def create_issue(self, *, token, owner, repo, request):
            raise RuntimeError("unexpected")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.create_issue._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.create_issue.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={
                "owner_name": "octocat",
                "repository_name": "Hello-World",
                "title": "Bug: cannot login",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert "unexpected" in result["response"]["error"]
    assert logger.error.await_count >= 2


@pytest.mark.asyncio
async def test_execute_invalid_config(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert logger.error.await_count >= 2
