import asyncio
from uuid import uuid4, UUID

import pytest

from app.integrations.github.create_pull_request import GitHubCreatePullRequestIntegration


class DummyLogger:
    async def error(self, msg: str):
        return None

    async def info(self, msg: str):
        return None


class DummyCredentialsResolver:
    def __init__(self, creds):
        self._creds = creds
        self.last_call = None

    async def get_default_for(self, bot_id: UUID, provider: str, strategy: str):
        self.last_call = {"bot_id": bot_id, "provider": provider, "strategy": strategy}
        return self._creds


def run(coro):
    """Запуск async-кода без pytest-asyncio."""
    return asyncio.run(coro)


def test_github_create_pr_httpx_not_available(monkeypatch):
    import app.integrations.github.create_pull_request as mod
    monkeypatch.setattr(mod, "HTTPX_AVAILABLE", False)

    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "x"}})

    result = run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "title": "t", "head": "h", "base": "b"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500


def test_github_create_pr_missing_required_config():
    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "x"}})

    result = run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World"},  # title/head/base отсутствуют
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


def test_github_create_pr_credentials_not_found():
    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds=None)

    result = run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "title": "t", "head": "h", "base": "b"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token" in result["response"]["description"].lower()


def test_github_create_pr_calls_resolver_with_other_provider():
    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds=None)

    run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "title": "t", "head": "h", "base": "b"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert resolver.last_call is not None
    assert resolver.last_call["provider"] == "other"
    assert resolver.last_call["strategy"] == "api_key"


def test_github_create_pr_token_missing_in_payload():
    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"something": "no-token"}})

    result = run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "title": "t", "head": "h", "base": "b"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token" in result["response"]["description"].lower()


def test_github_create_pr_success_payload_mapping(monkeypatch):
    """
    Проверяем:
    - draft_mode=yes -> payload содержит draft=True
    - maintainer_can_modify_mode=no -> payload содержит maintainer_can_modify=False
    - body передаётся
    - url правильный
    """
    import app.integrations.github.create_pull_request as mod

    captured = {}

    class FakeResponse:
        status_code = 201
        def json(self):
            return {"number": 10, "title": "PR"}

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = run(integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "title": "My PR",
            "head": "feature",
            "base": "main",
            "body": "test",
            "draft_mode": "yes",
            "maintainer_can_modify_mode": "no",
        },
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["number"] == 10

    assert captured["url"].endswith("/repos/octocat/Hello-World/pulls")
    assert captured["json"]["title"] == "My PR"
    assert captured["json"]["head"] == "feature"
    assert captured["json"]["base"] == "main"
    assert captured["json"]["body"] == "test"
    assert captured["json"]["draft"] is True
    assert captured["json"]["maintainer_can_modify"] is False
    assert "Authorization" in (captured["headers"] or {})


def test_github_create_pr_defaults_mapping(monkeypatch):
    """
    По умолчанию:
    - draft_mode=missing -> draft НЕ отправляем
    - maintainer_can_modify_mode=missing -> maintainer_can_modify отправляем True (как в коде)
    """
    import app.integrations.github.create_pull_request as mod

    captured = {}

    class FakeResponse:
        status_code = 201
        def json(self):
            return {"number": 1}

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url, json=None, headers=None):
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = run(integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "title": "My PR",
            "head": "feature",
            "base": "main",
        },
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is True
    assert "draft" not in captured["json"]
    assert captured["json"]["maintainer_can_modify"] is True


def test_github_create_pr_api_error(monkeypatch):
    import app.integrations.github.create_pull_request as mod

    class FakeResponse:
        status_code = 422
        def json(self):
            return {"message": "Validation Failed"}
        @property
        def text(self):
            return "Validation Failed"

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url, json=None, headers=None):
            return FakeResponse()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "title": "t", "head": "h", "base": "b"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 422
    assert "validation" in result["response"]["description"].lower()


def test_github_create_pr_timeout(monkeypatch):
    import app.integrations.github.create_pull_request as mod

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url, json=None, headers=None):
            raise mod.httpx.TimeoutException("timeout")  # type: ignore

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "title": "t", "head": "h", "base": "b"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 504


def test_github_create_pr_request_error(monkeypatch):
    import app.integrations.github.create_pull_request as mod

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url, json=None, headers=None):
            raise mod.httpx.RequestError("network")  # type: ignore

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubCreatePullRequestIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = run(integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "title": "t", "head": "h", "base": "b"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    ))

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 502
