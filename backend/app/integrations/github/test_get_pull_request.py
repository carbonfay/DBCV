import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.github.get_pull_request import GitHubGetPullRequestIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class DummyPullRequest:
    def to_dict(self):
        return {"id": 1, "number": 1347, "title": "PR title"}


class DummyPullRequestNoToDict(dict):
    pass


class DummyApiException(Exception):
    def __init__(self, status=None, message="api error"):
        super().__init__(message)
        self.status = status


@pytest.fixture
def integration():
    return GitHubGetPullRequestIntegration()


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
    assert md.id == "github_get_pull_request"
    assert md.version == "1.0.0"
    assert md.name == "GitHub Get Pull Request"
    assert md.category == "storage"
    assert md.credentials_provider == "other"
    assert md.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_github_execute_success_to_dict(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def get_pull_request(self, *, token, owner, repo, pull_number):
            assert token == "t"
            assert owner == "octocat"
            assert repo == "Hello-World"
            assert pull_number == 1347
            return DummyPullRequest()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_pull_request._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_pull_request.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World", "pull_number": 1347},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {"id": 1, "number": 1347, "title": "PR title"}
    logger.error.assert_not_awaited()


@pytest.mark.asyncio
async def test_github_execute_success_no_to_dict(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def get_pull_request(self, *, token, owner, repo, pull_number):
            return DummyPullRequestNoToDict({"k": "v"})

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_pull_request._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_pull_request.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World", "pull_number": 1347},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {"k": "v"}
    logger.error.assert_not_awaited()


@pytest.mark.asyncio
async def test_github_execute_token_not_found(integration, credentials_resolver, logger, bot_id):
    from app.integrations.github.get_pull_request import GitHubTokenNotFoundError

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        raise GitHubTokenNotFoundError("no token")

    with patch("app.integrations.github.get_pull_request._resolve_github_token", new=fake_resolve_token):
        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World", "pull_number": 1347},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "no token" in result["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_github_execute_credentials_not_found(integration, credentials_resolver, logger, bot_id):
    from app.integrations.github.get_pull_request import GitHubCredentialsNotFoundError

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        raise GitHubCredentialsNotFoundError("no creds")

    with patch("app.integrations.github.get_pull_request._resolve_github_token", new=fake_resolve_token):
        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World", "pull_number": 1347},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "no creds" in result["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_github_execute_api_exception_with_status(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def get_pull_request(self, *, token, owner, repo, pull_number):
            raise DummyApiException(status=404, message="Not Found")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_pull_request.ApiException", DummyApiException), \
         patch("app.integrations.github.get_pull_request._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_pull_request.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World", "pull_number": 999999},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404
    assert "Not Found" in result["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_github_execute_api_exception_without_status(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def get_pull_request(self, *, token, owner, repo, pull_number):
            raise DummyApiException(status=None, message="Boom")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_pull_request.ApiException", DummyApiException), \
         patch("app.integrations.github.get_pull_request._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_pull_request.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World", "pull_number": 1347},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_github_execute_unexpected_exception(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def get_pull_request(self, *, token, owner, repo, pull_number):
            raise RuntimeError("unexpected")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_pull_request._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_pull_request.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World", "pull_number": 1347},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert "unexpected" in result["response"]["error"]
    assert logger.error.await_count >= 2


@pytest.mark.asyncio
async def test_github_execute_invalid_config(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert logger.error.await_count >= 2