from __future__ import annotations

from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_github_service_list_commits_passes_kwargs_to_repos_api(monkeypatch):
    import app.integrations.github.service as svc

    entered = {"ok": False}
    exited = {"ok": False}

    class DummyApiClient:
        async def __aenter__(self):
            entered["ok"] = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            exited["ok"] = True
            return False

    calls = {"owner": None, "repo": None, "kwargs": None}

    class DummyReposApi:
        def __init__(self, api_client):
            assert api_client is dummy_client

        async def repos_list_commits(self, owner, repo, **kwargs):
            calls["owner"] = owner
            calls["repo"] = repo
            calls["kwargs"] = kwargs
            return [{"ok": True}]

    dummy_client = DummyApiClient()
    service = svc.GitHubService(settings=svc.GitHubClientSettings(host="https://h", retries=1))

    monkeypatch.setattr(service, "_api_client", lambda *, token: dummy_client)
    monkeypatch.setattr(svc, "ReposApi", DummyReposApi)

    since = datetime(2025, 1, 1, tzinfo=timezone.utc)
    until = datetime(2025, 2, 1, tzinfo=timezone.utc)

    res = await service.list_commits(
        token="t",
        owner="octocat",
        repo="Hello-World",
        sha="main",
        path="README.md",
        author="octocat",
        committer="octocat",
        since=since,
        until=until,
        per_page=100,
        page=3,
    )

    assert entered["ok"] is True
    assert exited["ok"] is True
    assert calls["owner"] == "octocat"
    assert calls["repo"] == "Hello-World"
    assert calls["kwargs"] == {
        "sha": "main",
        "path": "README.md",
        "author": "octocat",
        "committer": "octocat",
        "since": since,
        "until": until,
        "per_page": 100,
        "page": 3,
    }
    assert res == [{"ok": True}]