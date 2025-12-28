# app/integrations/github/service.py (update only the list_commits method)
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from app.integrations.github.github_adapter.github_openapi_client.api.repos_api import ReposApi
from app.integrations.github.github_adapter.github_openapi_client.api_client import ApiClient
from app.integrations.github.github_adapter.github_openapi_client.configuration import Configuration
from app.integrations.github.github_adapter.github_openapi_client.models.commit import Commit


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

    async def list_commits(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        sha: Optional[str] = None,
        path: Optional[str] = None,
        author: Optional[str] = None,
        committer: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        per_page: Optional[int] = None,
        page: Optional[int] = None,
    ) -> List[Commit]:
        async with self._api_client(token=token) as api_client:
            return await ReposApi(api_client).repos_list_commits(
                owner,
                repo,
                sha=sha,
                path=path,
                author=author,
                committer=committer,
                since=since,
                until=until,
                per_page=per_page,
                page=page,
            )


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
