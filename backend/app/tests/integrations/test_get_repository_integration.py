import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.github.get_repository import GitHubGetRepositoryIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class DummyRepo:
    def to_dict(self):
        return {"id": 1, "name": "Hello-World"}


class DummyRepoNoToDict(dict):
    pass


class DummyApiException(Exception):
    def __init__(self, status=None, message="api error"):
        super().__init__(message)
        self.status = status


@pytest.fixture
def integration():
    return GitHubGetRepositoryIntegration()


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

    assert md.id == "github_get_repository"
    assert md.version == "1.0.0"
    assert md.name == "GitHub Get Repository"
    assert md.category == "storage"
    assert md.credentials_provider == "other"
    assert md.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_github_execute_success_to_dict(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def get_repository(self, *, token, owner, repo):
            assert token == "t"
            assert owner == "octocat"
            assert repo == "Hello-World"
            return DummyRepo()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_repository._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_repository.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {"id": 1, "name": "Hello-World"}
    logger.error.assert_not_awaited()


@pytest.mark.asyncio
async def test_github_execute_success_no_to_dict(integration, credentials_resolver, logger, bot_id):
    class DummyService:
        async def get_repository(self, *, token, owner, repo):
            return DummyRepoNoToDict({"k": "v"})

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_repository._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_repository.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == {"k": "v"}
    logger.error.assert_not_awaited()


@pytest.mark.asyncio
async def test_github_execute_token_not_found(integration, credentials_resolver, logger, bot_id):
    from app.integrations.github.get_repository import GitHubTokenNotFoundError

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        raise GitHubTokenNotFoundError("no token")

    with patch("app.integrations.github.get_repository._resolve_github_token", new=fake_resolve_token):
        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World"},
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
    from app.integrations.github.get_repository import GitHubCredentialsNotFoundError

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        raise GitHubCredentialsNotFoundError("no creds")

    with patch("app.integrations.github.get_repository._resolve_github_token", new=fake_resolve_token):
        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World"},
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
        async def get_repository(self, *, token, owner, repo):
            raise DummyApiException(status=404, message="Not Found")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_repository.ApiException", DummyApiException), \
         patch("app.integrations.github.get_repository._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_repository.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Missing"},
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
        async def get_repository(self, *, token, owner, repo):
            raise DummyApiException(status=None, message="Boom")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_repository.ApiException", DummyApiException), \
         patch("app.integrations.github.get_repository._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_repository.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World"},
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
        async def get_repository(self, *, token, owner, repo):
            raise RuntimeError("unexpected")

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "t"

    with patch("app.integrations.github.get_repository._resolve_github_token", new=fake_resolve_token), \
         patch("app.integrations.github.get_repository.get_github_service", return_value=DummyService()):

        result = await integration.execute(
            config={"owner_name": "octocat", "repository_name": "Hello-World"},
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
