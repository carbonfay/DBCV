from typing import Optional, Any
from uuid import UUID

from app.auth.credentials_resolver import CredentialsResolver


class GitHubCredentialsNotFoundError(Exception):
    pass


class GitHubTokenNotFoundError(Exception):
    pass


async def _resolve_github_token(*, credentials_resolver: CredentialsResolver, bot_id: UUID) -> str:
    credentials = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")
    if not credentials:
        raise GitHubCredentialsNotFoundError("GitHub credentials not found")

    payload: Optional[dict[str, Any]] = credentials.get("payload") if isinstance(credentials, dict) else None
    effective_payload = payload if payload else credentials

    if not isinstance(effective_payload, dict):
        raise GitHubTokenNotFoundError("GitHub token payload is invalid")

    github_token = effective_payload.get("token") or effective_payload.get("access_token") or effective_payload.get("github_token")
    if not github_token or not isinstance(github_token, str):
        raise GitHubTokenNotFoundError("GitHub token not found in credentials payload")

    return github_token
