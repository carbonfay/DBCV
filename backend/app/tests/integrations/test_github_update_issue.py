import pytest
from uuid import uuid4, UUID

from app.integrations.github.update_issue import GitHubUpdateIssueIntegration


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


@pytest.mark.asyncio
async def test_github_update_issue_httpx_not_available(monkeypatch):
    import app.integrations.github.update_issue as mod
    monkeypatch.setattr(mod, "HTTPX_AVAILABLE", False)

    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "x"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1, "title": "New"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500


@pytest.mark.asyncio
async def test_github_update_issue_missing_required_config():
    integration = GitHubUpdateIssueIntegration()
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
async def test_github_update_issue_invalid_issue_number():
    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "x"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 0, "title": "New"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_github_update_issue_no_fields_to_update():
    """
    Если owner/repo/issue_number есть, но нет ни одного поля для обновления -> 400.
    """
    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "x"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "at least one field" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_github_update_issue_credentials_not_found():
    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds=None)

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1, "title": "New"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_github_update_issue_calls_resolver_with_other_provider():
    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds=None)

    await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1, "title": "New"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert resolver.last_call is not None
    assert resolver.last_call["provider"] == "other"
    assert resolver.last_call["strategy"] == "api_key"
    assert isinstance(resolver.last_call["bot_id"], UUID)


@pytest.mark.asyncio
async def test_github_update_issue_token_missing_in_payload():
    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"something": "no-token"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1, "title": "New"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_github_update_issue_success(monkeypatch):
    """
    PATCH должен уйти с json=payload (только обновляемые поля) и вернуть ok True.
    """
    import app.integrations.github.update_issue as mod

    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"number": 1, "title": "Updated"}

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def patch(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "issue_number": 1,
            "title": "Updated",
            "state": "closed",
        },
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["title"] == "Updated"

    assert "/repos/octocat/Hello-World/issues/1" in captured["url"]
    assert captured["json"] == {"title": "Updated", "state": "closed"}
    assert "Authorization" in (captured["headers"] or {})


@pytest.mark.asyncio
async def test_github_update_issue_api_error(monkeypatch):
    import app.integrations.github.update_issue as mod

    class FakeResponse:
        status_code = 403

        def json(self):
            return {"message": "Forbidden"}

        @property
        def text(self):
            return "Forbidden"

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def patch(self, url, json=None, headers=None):
            return FakeResponse()

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1, "title": "Updated"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 403
    assert "forbidden" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_github_update_issue_timeout(monkeypatch):
    import app.integrations.github.update_issue as mod

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def patch(self, url, json=None, headers=None):
            raise mod.httpx.TimeoutException("timeout")  # type: ignore

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1, "title": "Updated"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 504


@pytest.mark.asyncio
async def test_github_update_issue_request_error(monkeypatch):
    import app.integrations.github.update_issue as mod

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def patch(self, url, json=None, headers=None):
            raise mod.httpx.RequestError("network")  # type: ignore

    monkeypatch.setattr(mod.httpx, "AsyncClient", FakeAsyncClient)

    integration = GitHubUpdateIssueIntegration()
    resolver = DummyCredentialsResolver(creds={"payload": {"api_key": "ghp_test"}})

    result = await integration.execute(
        config={"owner": "octocat", "repo": "Hello-World", "issue_number": 1, "title": "Updated"},
        credentials_resolver=resolver,
        bot_id=uuid4(),
        logger=DummyLogger(),
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 502
