import pytest
from uuid import uuid4, UUID

from app.integrations.github.get_issue import GitHubGetIssueIntegration


class DummyLogger:
    async def error(self, msg: str):
        return None

    async def info(self, msg: str):
        return None


class DummyCredentialsResolver:
    def __init__(self, creds):
        self._creds = creds
        self.last_call = None  # чтобы можно было проверять параметры вызова

    async def get_default_for(self, bot_id: UUID, provider: str, strategy: str):
        self.last_call = {"bot_id": bot_id, "provider": provider, "strategy": strategy}
        return self._creds


@pytest.mark.asyncio
async def test_github_get_issue_httpx_not_available(monkeypatch):
    import app.integrations.github.get_issue as mod

    monkeypatch.setattr(mod, "HTTPX_AVAILABLE", False)

    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "x"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500


@pytest.mark.asyncio
async def test_github_get_issue_missing_required_config():
    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "x"}})

    result = await integration.execute(
        config={"owner": "octocat"},  # repo/issue_number отсутствуют
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_github_get_issue_credentials_not_found():
    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds=None)

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_github_get_issue_calls_resolver_with_other_provider():
    """
    Проверяем, что интеграция ищет credentials именно по provider='other' и strategy='api_key'.
    """
    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds=None)

    await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert resolver.last_call is not None
    assert resolver.last_call["provider"] == "other"
    assert resolver.last_call["strategy"] == "api_key"
    assert isinstance(resolver.last_call["bot_id"], UUID)


@pytest.mark.asyncio
async def test_github_get_issue_token_missing_in_payload():
    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"something": "no-token"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_github_get_issue_success(monkeypatch):
    import app.integrations.github.get_issue as mod

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"number": 1, "title": "Test Issue"}

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            assert "Authorization" in (headers or {})
            return FakeResponse()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["title"] == "Test Issue"


@pytest.mark.asyncio
async def test_github_get_issue_api_error(monkeypatch):
    import app.integrations.github.get_issue as mod

    class FakeResponse:
        status_code = 404

        def json(self):
            return {"message": "Not Found"}

        @property
        def text(self):
            return "Not Found"

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            return FakeResponse()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 999999},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_github_get_issue_timeout(monkeypatch):
    import app.integrations.github.get_issue as mod

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            raise mod.httpx.TimeoutException("timeout")  # type: ignore

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 504


@pytest.mark.asyncio
async def test_github_get_issue_request_error(monkeypatch):
    import app.integrations.github.get_issue as mod

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            raise mod.httpx.RequestError("network")  # type: ignore

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubGetIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 502
