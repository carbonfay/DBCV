from __future__ import annotations

from uuid import UUID

import pytest


class DummyCredentialsResolver:
    def __init__(self, value):
        self._value = value
        self.calls = []

    async def get_default_for(self, *, bot_id, provider, strategy):
        self.calls.append((bot_id, provider, strategy))
        return self._value


@pytest.mark.asyncio
async def test_resolve_github_token_credentials_missing():
    from app.integrations.github.token_resolver import _resolve_github_token, GitHubCredentialsNotFoundError

    resolver = DummyCredentialsResolver(None)

    with pytest.raises(GitHubCredentialsNotFoundError) as e:
        await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))

    assert "GitHub credentials not found" in str(e.value)
    assert resolver.calls == [(UUID(int=0), "other", "api_key")]


@pytest.mark.asyncio
async def test_resolve_github_token_invalid_payload_type():
    from app.integrations.github.token_resolver import _resolve_github_token, GitHubTokenNotFoundError

    resolver = DummyCredentialsResolver(["not-a-dict"])

    with pytest.raises(GitHubTokenNotFoundError) as e:
        await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))

    assert "payload is invalid" in str(e.value)


@pytest.mark.asyncio
async def test_resolve_github_token_dict_without_payload_uses_top_level_token():
    from app.integrations.github.token_resolver import _resolve_github_token

    resolver = DummyCredentialsResolver({"token": "t"})
    token = await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))
    assert token == "t"


@pytest.mark.asyncio
async def test_resolve_github_token_dict_payload_token_priority():
    from app.integrations.github.token_resolver import _resolve_github_token

    resolver = DummyCredentialsResolver({"payload": {"token": "t1", "access_token": "t2", "github_token": "t3"}})
    token = await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))
    assert token == "t1"


@pytest.mark.asyncio
async def test_resolve_github_token_dict_payload_access_token_fallback():
    from app.integrations.github.token_resolver import _resolve_github_token

    resolver = DummyCredentialsResolver({"payload": {"access_token": "t2", "github_token": "t3"}})
    token = await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))
    assert token == "t2"


@pytest.mark.asyncio
async def test_resolve_github_token_dict_payload_github_token_fallback():
    from app.integrations.github.token_resolver import _resolve_github_token

    resolver = DummyCredentialsResolver({"payload": {"github_token": "t3"}})
    token = await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))
    assert token == "t3"


@pytest.mark.asyncio
async def test_resolve_github_token_missing_token_fields():
    from app.integrations.github.token_resolver import _resolve_github_token, GitHubTokenNotFoundError

    resolver = DummyCredentialsResolver({"payload": {"nope": "x"}})

    with pytest.raises(GitHubTokenNotFoundError) as e:
        await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))

    assert "token not found" in str(e.value)


@pytest.mark.asyncio
async def test_resolve_github_token_token_not_str():
    from app.integrations.github.token_resolver import _resolve_github_token, GitHubTokenNotFoundError

    resolver = DummyCredentialsResolver({"payload": {"token": 123}})

    with pytest.raises(GitHubTokenNotFoundError) as e:
        await _resolve_github_token(credentials_resolver=resolver, bot_id=UUID(int=0))

    assert "token not found" in str(e.value)
