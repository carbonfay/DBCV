import pytest


@pytest.mark.asyncio
async def test_github_service_get_pull_request_uses_api_client_context_and_calls_pulls_api(monkeypatch):
    import app.integrations.github.service as svc

    entered = {"ok": False}
    exited = {"ok": False}
    calls = {"args": None}

    class DummyApiClient:
        async def __aenter__(self):
            entered["ok"] = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            exited["ok"] = True
            return False

    dummy_client = DummyApiClient()

    class DummyPullsApi:
        def __init__(self, api_client):
            assert api_client is dummy_client

        async def pulls_get(self, owner, repo, pull_number):
            calls["args"] = (owner, repo, pull_number)
            return {"owner": owner, "repo": repo, "pull_number": pull_number}

    service = svc.GitHubService(settings=svc.GitHubClientSettings(host="https://h", retries=1))

    monkeypatch.setattr(service, "_api_client", lambda *, token: dummy_client)
    monkeypatch.setattr(svc, "PullsApi", DummyPullsApi)

    res = await service.get_pull_request(token="t", owner="octocat", repo="Hello-World", pull_number=1347)
    assert entered["ok"] is True
    assert exited["ok"] is True
    assert calls["args"] == ("octocat", "Hello-World", 1347)
    assert res == {"owner": "octocat", "repo": "Hello-World", "pull_number": 1347}