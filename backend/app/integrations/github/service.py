from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Optional
from app.integrations.github.github_adapter.github_openapi_client.api_client import ApiClient
from app.integrations.github.github_adapter.github_openapi_client.configuration import Configuration
from app.integrations.github.github_adapter.github_openapi_client.api.issues_api import IssuesApi
from app.integrations.github.github_adapter.github_openapi_client.models.issue import Issue
from app.integrations.github.github_adapter.github_openapi_client.models.issues_create_request import IssuesCreateRequest

@dataclass(frozen=True)
class GitHubClientSettings:
    host: str = "https://api.github.com"
    retries: int = 3


def _build_configuration(*, token: str, settings: GitHubClientSettings) -> Configuration:
    cfg = Configuration(host=settings.host)
    cfg.retries = settings.retries
    cfg.access_token = token
    return cfg


class GitHubService:
    def __init__(self, *, settings: GitHubClientSettings) -> None:
        self._settings = settings

    def _api_client(self, *, token: str) -> ApiClient:
        return ApiClient(_build_configuration(token=token, settings=self._settings))

    async def create_issue(
            self,
            *,
            token: str,
            owner: str,
            repo: str,
            request: IssuesCreateRequest,
    ) -> Issue:
        headers = {"Authorization": f"Bearer {token}"}
        async with self._api_client(token=token) as api_client:
            return await IssuesApi(api_client).issues_create(owner, repo, request, _headers=headers)

_service_lock = threading.Lock()
_service_instance: Optional[GitHubService] = None


def get_github_service() -> GitHubService:
    global _service_instance
    if _service_instance is not None:
        return _service_instance

    with _service_lock:
        if _service_instance is None:
            host = os.getenv("GITHUB_HOST", "https://api.github.com")
            retries = int(os.getenv("GITHUB_RETRIES", "3"))
            _service_instance = GitHubService(settings=GitHubClientSettings(host=host, retries=retries))
        return _service_instance
