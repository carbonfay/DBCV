from __future__ import annotations

from uuid import UUID
from unittest.mock import AsyncMock

import pytest


class DummyRepo:
    def to_dict(self):
        return {"id": 1, "name": "Hello-World"}


class DummyRepoNoToDict(dict):
    pass


class DummyApiException(Exception):
    def __init__(self, status=None, message="api error"):
        super().__init__(message)
        self.status = status


@pytest.mark.asyncio
async def test_execute_success_to_dict(monkeypatch):
    from app.integrations.github.get_repository import GitHubGetRepositoryIntegration

    integration = GitHubGetRepositoryIntegration()
    logger = AsyncMock()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "token"

    class DummyService:
        async def get_repository(self, *, token, owner, repo):
            assert token == "token"
            assert owner == "octocat"
            assert repo == "Hello-World"
            return DummyRepo()

    monkeypatch.setattr("app.integrations.github.get_repository._resolve_github_token", fake_resolve_token)
    monkeypatch.setattr("app.integrations.github.get_repository.get_github_service", lambda: DummyService())

    res = await integration.execute(
        config={"owner_name": "octocat", "repository_name": "Hello-World"},
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res == {"response": {"ok": True, "result": {"id": 1, "name": "Hello-World"}}}
    logger.error.assert_not_called()


@pytest.mark.asyncio
async def test_execute_success_no_to_dict(monkeypatch):
    from app.integrations.github.get_repository import GitHubGetRepositoryIntegration

    integration = GitHubGetRepositoryIntegration()
    logger = AsyncMock()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "token"

    class DummyService:
        async def get_repository(self, *, token, owner, repo):
            return DummyRepoNoToDict({"k": "v"})

    monkeypatch.setattr("app.integrations.github.get_repository._resolve_github_token", fake_resolve_token)
    monkeypatch.setattr("app.integrations.github.get_repository.get_github_service", lambda: DummyService())

    res = await integration.execute(
        config={"owner_name": "octocat", "repository_name": "Hello-World"},
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res["response"]["ok"] is True
    assert res["response"]["result"] == {"k": "v"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc_class_name",
    ["GitHubTokenNotFoundError", "GitHubCredentialsNotFoundError"],
)
async def test_execute_token_resolver_errors(monkeypatch, exc_class_name):
    import app.integrations.github.get_repository as mod

    integration = mod.GitHubGetRepositoryIntegration()
    logger = AsyncMock()

    exc_cls = getattr(mod, exc_class_name)

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        raise exc_cls("no token")

    monkeypatch.setattr("app.integrations.github.get_repository._resolve_github_token", fake_resolve_token)

    res = await integration.execute(
        config={"owner_name": "octocat", "repository_name": "Hello-World"},
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res["response"]["ok"] is False
    assert res["response"]["error_code"] == 401
    assert "no token" in res["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_execute_api_exception_with_status(monkeypatch):
    import app.integrations.github.get_repository as mod

    integration = mod.GitHubGetRepositoryIntegration()
    logger = AsyncMock()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "token"

    class DummyService:
        async def get_repository(self, *, token, owner, repo):
            raise DummyApiException(status=404, message="Not Found")

    monkeypatch.setattr("app.integrations.github.get_repository.ApiException", DummyApiException)
    monkeypatch.setattr("app.integrations.github.get_repository._resolve_github_token", fake_resolve_token)
    monkeypatch.setattr("app.integrations.github.get_repository.get_github_service", lambda: DummyService())

    res = await integration.execute(
        config={"owner_name": "octocat", "repository_name": "Missing"},
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res["response"]["ok"] is False
    assert res["response"]["error_code"] == 404
    assert "Not Found" in res["response"]["error"]
    logger.error.assert_awaited()


@pytest.mark.asyncio
async def test_execute_api_exception_without_status(monkeypatch):
    import app.integrations.github.get_repository as mod

    integration = mod.GitHubGetRepositoryIntegration()
    logger = AsyncMock()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "token"

    class DummyService:
        async def get_repository(self, *, token, owner, repo):
            raise DummyApiException(status=None, message="Boom")

    monkeypatch.setattr("app.integrations.github.get_repository.ApiException", DummyApiException)
    monkeypatch.setattr("app.integrations.github.get_repository._resolve_github_token", fake_resolve_token)
    monkeypatch.setattr("app.integrations.github.get_repository.get_github_service", lambda: DummyService())

    res = await integration.execute(
        config={"owner_name": "octocat", "repository_name": "Hello-World"},
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res["response"]["ok"] is False
    assert res["response"]["error_code"] == 500


@pytest.mark.asyncio
async def test_execute_unexpected_exception(monkeypatch):
    from app.integrations.github.get_repository import GitHubGetRepositoryIntegration

    integration = GitHubGetRepositoryIntegration()
    logger = AsyncMock()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "token"

    class DummyService:
        async def get_repository(self, *, token, owner, repo):
            raise RuntimeError("unexpected")

    monkeypatch.setattr("app.integrations.github.get_repository._resolve_github_token", fake_resolve_token)
    monkeypatch.setattr("app.integrations.github.get_repository.get_github_service", lambda: DummyService())

    res = await integration.execute(
        config={"owner_name": "octocat", "repository_name": "Hello-World"},
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res["response"]["ok"] is False
    assert res["response"]["error_code"] == 500
    assert logger.error.await_count >= 2


@pytest.mark.asyncio
async def test_execute_invalid_config_validation_error(monkeypatch):
    from app.integrations.github.get_repository import GitHubGetRepositoryIntegration

    integration = GitHubGetRepositoryIntegration()
    logger = AsyncMock()

    res = await integration.execute(
        config={"owner_name": "", "repository_name": ""},
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res["response"]["ok"] is False
    assert res["response"]["error_code"] == 500
    assert logger.error.await_count >= 2


def test_metadata_contains_expected_fields():
    from app.integrations.github.get_repository import GitHubGetRepositoryIntegration

    md = GitHubGetRepositoryIntegration().metadata
    assert md.id == "github_get_repository"
    assert md.version == "1.0.0"
    assert md.credentials_provider == "other"
    assert md.credentials_strategy == "api_key"

