from __future__ import annotations

import importlib
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_build_configuration_sets_fields():
    from app.integrations.github.service import _build_configuration, GitHubClientSettings

    cfg = _build_configuration(token="t", settings=GitHubClientSettings(host="https://h", retries=7))
    assert cfg.host == "https://h"
    assert cfg.retries == 7
    assert cfg.access_token == "t"


def test_get_github_service_caches_instance_and_reads_env(monkeypatch):
    import app.integrations.github.service as svc

    monkeypatch.setenv("GITHUB_HOST", "https://api.github.com")
    monkeypatch.setenv("GITHUB_RETRIES", "5")

    svc._service_instance = None

    s1 = svc.get_github_service()
    s2 = svc.get_github_service()

    assert s1 is s2
    assert s1._settings.host == "https://api.github.com"
    assert s1._settings.retries == 5


def test_get_github_service_default_env_values(monkeypatch):
    import app.integrations.github.service as svc

    monkeypatch.delenv("GITHUB_HOST", raising=False)
    monkeypatch.delenv("GITHUB_RETRIES", raising=False)

    svc._service_instance = None
    s = svc.get_github_service()

    assert s._settings.host == "https://api.github.com"
    assert s._settings.retries == 3


def test_get_github_service_thread_lock_path(monkeypatch):
    import app.integrations.github.service as svc

    monkeypatch.setenv("GITHUB_HOST", "https://x")
    monkeypatch.setenv("GITHUB_RETRIES", "2")

    svc._service_instance = None

    class DummyLock:
        def __init__(self):
            self.entered = 0

        def __enter__(self):
            self.entered += 1

        def __exit__(self, exc_type, exc, tb):
            return False

    lock = DummyLock()
    monkeypatch.setattr(svc, "_service_lock", lock)

    s = svc.get_github_service()
    assert s._settings.host == "https://x"
    assert s._settings.retries == 2
    assert lock.entered == 1

    s2 = svc.get_github_service()
    assert s2 is s
    assert lock.entered == 1


@pytest.mark.asyncio
async def test_github_service_get_repository_uses_api_client_context_and_calls_repos_api(monkeypatch):
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

    calls = {"args": None}

    class DummyReposApi:
        def __init__(self, api_client):
            assert api_client is dummy_client

        async def repos_get(self, owner, repo):
            calls["args"] = (owner, repo)
            return {"owner": owner, "repo": repo}

    dummy_client = DummyApiClient()
    service = svc.GitHubService(settings=svc.GitHubClientSettings(host="https://h", retries=1))

    monkeypatch.setattr(service, "_api_client", lambda *, token: dummy_client)
    monkeypatch.setattr(svc, "ReposApi", DummyReposApi)

    res = await service.get_repository(token="t", owner="octocat", repo="Hello-World")
    assert entered["ok"] is True
    assert exited["ok"] is True
    assert calls["args"] == ("octocat", "Hello-World")
    assert res == {"owner": "octocat", "repo": "Hello-World"}
