from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

from app.integrations.github.service import get_github_service
from app.integrations.github.token_resolver import (
    GitHubCredentialsNotFoundError,
    GitHubTokenNotFoundError,
    _resolve_github_token,
)

from app.integrations.github.github_adapter.github_openapi_client.models.issues_create_request import   IssuesCreateRequest
from app.integrations.github.github_adapter.github_openapi_client.models.issues_create_request_title import    IssuesCreateRequestTitle
from app.integrations.github.github_adapter.github_openapi_client.models.issues_create_request_labels_inner import  IssuesCreateRequestLabelsInner
from app.integrations.github.github_adapter.github_openapi_client.models.issues_create_request_milestone import IssuesCreateRequestMilestone
from app.integrations.github.github_adapter.github_openapi_client.exceptions import ApiException


def _coerce_oneof_title(value: str | int | IssuesCreateRequestTitle) -> IssuesCreateRequestTitle:
    if isinstance(value, IssuesCreateRequestTitle):
        return value
    return IssuesCreateRequestTitle(value)


def _coerce_label(value: str | IssuesCreateRequestLabelsInner) -> IssuesCreateRequestLabelsInner:
    if isinstance(value, IssuesCreateRequestLabelsInner):
        return value
    try:
        return IssuesCreateRequestLabelsInner.model_validate(value)
    except Exception:
        key = next(iter(IssuesCreateRequestLabelsInner.model_fields.keys()))
        return IssuesCreateRequestLabelsInner.model_validate({key: value})


def _coerce_milestone(value: int | IssuesCreateRequestMilestone) -> IssuesCreateRequestMilestone:
    if isinstance(value, IssuesCreateRequestMilestone):
        return value
    try:
        return IssuesCreateRequestMilestone.model_validate(value)
    except Exception:
        key = next(iter(IssuesCreateRequestMilestone.model_fields.keys()))
        return IssuesCreateRequestMilestone.model_validate({key: value})


class GitHubCreateIssueIntegrationConfiguration(BaseModel):
    owner_name: str = Field(min_length=1)
    repository_name: str = Field(min_length=1)

    title: str = Field(min_length=1)
    body: Optional[str] = None

    assignee: Optional[str] = None
    assignees: Optional[List[str]] = None

    labels: Optional[List[str]] = None
    milestone: Optional[int] = None

    type: Optional[str] = None


class GitHubCreateIssueIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_issue",
            version="1.0.0",
            name="GitHub Create Issue",
            description="Create an issue by owner and repository name",
            category="storage",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema=GitHubCreateIssueIntegrationConfiguration.model_json_schema(),
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="DBCV.backend.app.integrations.github.github_adapter.github_openapi_client",
            examples=[
                {
                    "title": "Create issue",
                    "config": {
                        "owner_name": "octocat",
                        "repository_name": "Hello-World",
                        "title": "Bug: cannot login",
                        "body": "Steps to reproduce: ...",
                        "labels": ["bug", "triage"],
                    },
                },
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
            cfg = GitHubCreateIssueIntegrationConfiguration.model_validate(config)
            token = await _resolve_github_token(credentials_resolver=credentials_resolver, bot_id=bot_id)

            service = get_github_service()
            req = IssuesCreateRequest(
                title=_coerce_oneof_title(cfg.title),
                body=cfg.body,
                assignee=cfg.assignee,
                assignees=cfg.assignees,
                labels=[_coerce_label(x) for x in (cfg.labels or [])] or None,
                milestone=_coerce_milestone(cfg.milestone) if cfg.milestone is not None else None,
                type=cfg.type,
            )
            issue = await service.create_issue(
                token=token,
                owner=cfg.owner_name,
                repo=cfg.repository_name,
                request=req,
            )
            if hasattr(issue, "to_dict") and callable(issue.to_dict):
                result = issue.to_dict()
            elif isinstance(issue, dict):
                result = issue
            else:
                result = getattr(issue, "__dict__", {"value": str(issue)})
            return {"response": {"ok": True, "result": result}}

        except (GitHubTokenNotFoundError, GitHubCredentialsNotFoundError) as e:
            await logger.error(f"github_create_issue auth: {e}")
            return {"response": {"ok": False, "error_code": 401, "error": str(e)}}

        except ApiException as e:
            code = getattr(e, "status", None) or 500
            await logger.error(f"github_create_issue api: {e}")
            return {"response": {"ok": False, "error_code": code, "error": str(e)}}

        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"github_create_issue unexpected: {e}")
            await logger.error(f"github_create_issue traceback:\n{tb}")
            return {"response": {"ok": False, "error_code": 500, "error": str(e)}}
