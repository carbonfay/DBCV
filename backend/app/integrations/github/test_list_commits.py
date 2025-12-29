from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from unittest.mock import AsyncMock

import pytest


class DummyCommit:
    def __init__(self, sha: str):
        self.sha = sha

    def to_dict(self):
        return {"sha": self.sha}


@pytest.mark.asyncio
async def test_execute_success_passes_optional_args(monkeypatch):
    from app.integrations.github.list_commits import GitHubListCommitsIntegration

    integration = GitHubListCommitsIntegration()
    logger = AsyncMock()

    async def fake_resolve_token(*, credentials_resolver, bot_id):
        return "token"

    since = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    until = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

    class DummyService:
        async def list_commits(
            self,
            *,
            token,
            owner,
            repo,
            sha=None,
            path=None,
            author=None,
            committer=None,
            since=None,
            until=None,
            per_page=None,
            page=None,
        ):
            assert token == "token"
            assert owner == "octocat"
            assert repo == "Hello-World"
            assert sha == "main"
            assert path == "README.md"
            assert author == "octocat"
            assert committer == "octocat"
            assert since == since
            assert until == until
            assert per_page == 50
            assert page == 2
            return [DummyCommit("a")]

    monkeypatch.setattr("app.integrations.github.list_commits._resolve_github_token", fake_resolve_token)
    monkeypatch.setattr("app.integrations.github.list_commits.get_github_service", lambda: DummyService())

    res = await integration.execute(
        config={
            "owner_name": "octocat",
            "repository_name": "Hello-World",
            "sha": "main",
            "path": "README.md",
            "author": "octocat",
            "committer": "octocat",
            "since": since.isoformat().replace("+00:00", "Z"),
            "until": until.isoformat().replace("+00:00", "Z"),
            "per_page": 50,
            "page": 2,
        },
        credentials_resolver=AsyncMock(),
        bot_id=UUID(int=0),
        logger=logger,
    )

    assert res == {"response": {"ok": True, "result": [{"sha": "a"}]}}
    logger.error.assert_not_called()