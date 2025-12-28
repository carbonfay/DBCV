from __future__ import annotations

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.github.token_resolver import (
    _resolve_github_token,
    GitHubCredentialsNotFoundError,
    GitHubTokenNotFoundError,
)
from app.loggers.bot import BotLogger

try:
    from app.integrations.github.service import get_github_service
    from .github_adapter.github_openapi_client.exceptions import ApiException

    ADAPTER_AVAILABLE = True
except ImportError as e:
    traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    logging.error(f"github_openapi_client not available traceback: \n{traceback_str}")
    logging.error(f"github_openapi_client not available: {e}")
    ADAPTER_AVAILABLE = False
    get_github_service = None
    ApiException = ImportError


class GitHubListCommitsIntegrationConfiguration(BaseModel):
    owner_name: str = Field(min_length=1)
    repository_name: str = Field(min_length=1)
    sha: Optional[str] = None
    path: Optional[str] = None
    author: Optional[str] = None
    committer: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    per_page: Optional[int] = Field(default=None, ge=1, le=100)
    page: Optional[int] = Field(default=None, ge=1)


class GitHubListCommitsIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_list_commits",
            version="1.0.0",
            name="GitHub List Commits",
            description="List commits by owner and repository name",
            category="storage",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema=GitHubListCommitsIntegrationConfiguration.model_json_schema(),
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="DBCV.backend.app.integrations.github.github_adapter.github_openapi_client"
            if ADAPTER_AVAILABLE
            else None,
            examples=[
                {
                    "title": "List Commits",
                    "config": {"owner_name": "octocat", "repository_name": "Hello-World"},
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        try:
            cfg = GitHubListCommitsIntegrationConfiguration.model_validate(config)
            token = await _resolve_github_token(credentials_resolver=credentials_resolver, bot_id=bot_id)

            service = get_github_service()
            commits = await service.list_commits(
                token=token,
                owner=cfg.owner_name,
                repo=cfg.repository_name,
                sha=cfg.sha,
                path=cfg.path,
                author=cfg.author,
                committer=cfg.committer,
                since=cfg.since,
                until=cfg.until,
                per_page=cfg.per_page,
                page=cfg.page,
            )

            result: List[Any] = []
            for c in commits:
                result.append(c.to_dict() if hasattr(c, "to_dict") else c)

            return {"response": {"ok": True, "result": result}}

        except (GitHubTokenNotFoundError, GitHubCredentialsNotFoundError) as e:
            await logger.error(f"github_list_commits token_resolver: {e}")
            return {"response": {"ok": False, "error_code": 401, "error": str(e)}}

        except ApiException as e:
            await logger.error(f"github_list_commits service.list_commits: {e}")
            status = getattr(e, "status", None)
            body = getattr(e, "body", None)
            return {
                "response": {
                    "ok": False,
                    "error_code": int(status) if status else 500,
                    "error": body if body else str(e),
                }
            }

        except Exception as e:
            traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"github_list_commits unexpected: {e}")
            await logger.error(f"github_list_commits traceback: \n{traceback_str}")
            return {"response": {"ok": False, "error_code": 500, "error": str(e)}}
