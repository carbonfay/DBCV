"""GitHub Create Pull Request интеграция с использованием httpx."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover - библиотека должна быть установлена
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore


class GitHubCreatePullRequestIntegration(BaseIntegration):
    """Интеграция для создания Pull Request в GitHub."""

    _GITHUB_API_URL = "https://api.github.com"

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_pull_request",
            version="1.0.0",
            name="GitHub Create Pull Request",
            description="Создание Pull Request в GitHub через REST API.",
            category="github",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292E",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title", "head", "base"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Repository Owner",
                        "description": "Логин пользователя или организации GitHub."
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository Name",
                        "description": "Название репозитория."
                    },
                    "title": {
                        "type": "string",
                        "title": "Pull Request Title",
                        "description": "Заголовок Pull Request."
                    },
                    "head": {
                        "type": "string",
                        "title": "Head Branch",
                        "description": "Ветка, из которой создается Pull Request (например, 'feature-branch' или 'owner:feature-branch' для форков)."
                    },
                    "base": {
                        "type": "string",
                        "title": "Base Branch",
                        "description": "Ветка, в которую создается Pull Request (обычно 'main' или 'master')."
                    },
                    "body": {
                        "type": "string",
                        "title": "Pull Request Body",
                        "description": "Описание Pull Request (опционально)."
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Создать Pull Request",
                    "config": {
                        "owner": "barsux",
                        "repo": "barsux",
                        "title": "Add new feature",
                        "head": "feature-branch",
                        "base": "main",
                        "body": "This PR adds a new feature to the project."
                    }
                },
                {
                    "title": "Создать черновик Pull Request",
                    "config": {
                        "owner": "barsux",
                        "repo": "barsux",
                        "title": "Work in progress",
                        "head": "wip-branch",
                        "base": "main",
                        "body": "This is a work in progress.",
                        "draft": True
                    }
                },
                {
                    "title": "Создать Pull Request из форка",
                    "config": {
                        "owner": "barsux",
                        "repo": "barsux",
                        "title": "Fix bug",
                        "head": "contributor:fix-branch",
                        "base": "main",
                        "body": "This PR fixes a critical bug.",
                        "maintainer_can_modify": True
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Создает Pull Request в GitHub.

        Returns:
            dict: {"response": {"ok": bool, "result": {...}}}
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not installed")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        try:
            owner = str(config.get("owner", "")).strip()
            repo = str(config.get("repo", "")).strip()
            title = str(config.get("title", "")).strip()
            head = str(config.get("head", "")).strip()
            base = str(config.get("base", "")).strip()
            credentials_id_raw = config.get("credentials_id")
        except ValueError:
            await logger.error("Failed to parse fields")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Incorrect field's values"
                }
            }

        if not owner or not repo:
            await logger.error("owner and repo are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner and repo are required"
                }
            }

        if not title:
            await logger.error("title is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "title is required"
                }
            }

        if not head:
            await logger.error("head is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "head is required"
                }
            }

        if not base:
            await logger.error("base is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "base is required"
                }
            }

        credentials_uuid: Optional[UUID] = None
        if credentials_id_raw:
            try:
                credentials_uuid = UUID(str(credentials_id_raw))
            except (TypeError, ValueError):
                await logger.error("credentials_id must be a valid UUID")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "credentials_id must be a valid UUID"
                    }
                }

        if credentials_uuid:
            creds = await credentials_resolver.get_by_id(credentials_uuid)
        else:
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="other",
                strategy="api_key"
            )

        if not creds:
            await logger.error("GitHub credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub credentials not found"
                }
            }

        payload = creds.get("payload") or creds
        token = payload.get("token") or payload.get("access_token") or payload.get("github_token") or payload.get("personal_access_token")

        if not token:
            await logger.error("GitHub access token not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub access token not found in credentials"
                }
            }

        # Формируем тело запроса для создания Pull Request
        create_payload: Dict[str, Any] = {
            "title": title,
            "head": head,
            "base": base
        }

        if "body" in config:
            body = config.get("body")
            if body is not None:
                create_payload["body"] = str(body)

        if "draft" in config:
            draft = config.get("draft")
            if draft is not None:
                if isinstance(draft, bool):
                    create_payload["draft"] = draft
                elif isinstance(draft, str):
                    draft_lower = draft.lower().strip()
                    if draft_lower in ["true", "1", "yes"]:
                        create_payload["draft"] = True
                    elif draft_lower in ["false", "0", "no"]:
                        create_payload["draft"] = False
                    else:
                        await logger.error(f"Invalid draft value: {draft}. Must be boolean or 'true'/'false'")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 400,
                                "description": "draft must be a boolean value"
                            }
                        }
                else:
                    await logger.error(f"Invalid draft value type: {type(draft)}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "draft must be a boolean value"
                        }
                    }

        if "maintainer_can_modify" in config:
            maintainer_can_modify = config.get("maintainer_can_modify")
            if maintainer_can_modify is not None:
                if isinstance(maintainer_can_modify, bool):
                    create_payload["maintainer_can_modify"] = maintainer_can_modify
                elif isinstance(maintainer_can_modify, str):
                    maintainer_can_modify_lower = maintainer_can_modify.lower().strip()
                    if maintainer_can_modify_lower in ["true", "1", "yes"]:
                        create_payload["maintainer_can_modify"] = True
                    elif maintainer_can_modify_lower in ["false", "0", "no"]:
                        create_payload["maintainer_can_modify"] = False
                    else:
                        await logger.error(f"Invalid maintainer_can_modify value: {maintainer_can_modify}")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 400,
                                "description": "maintainer_can_modify must be a boolean value"
                            }
                        }
                else:
                    await logger.error(f"Invalid maintainer_can_modify value type: {type(maintainer_can_modify)}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "maintainer_can_modify must be a boolean value"
                        }
                    }

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DBCV-GitHub-Integration"
        }

        timeout = httpx.Timeout(15.0, connect=5.0)

        try:
            async with httpx.AsyncClient(base_url=self._GITHUB_API_URL, timeout=timeout) as client:
                create_response = await client.post(
                    f"/repos/{owner}/{repo}/pulls",
                    headers=headers,
                    json=create_payload
                )

                if create_response.status_code >= 400:
                    error_description = self._extract_error_description(create_response)
                    await logger.error(f"GitHub API error {create_response.status_code}: {error_description}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": create_response.status_code,
                            "description": error_description
                        }
                    }

                try:
                    pr_payload = create_response.json()
                except ValueError:
                    await logger.error("Unable to parse GitHub pull request response as JSON")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": "Unable to parse GitHub pull request response"
                        }
                    }

                formatted_pr = self._build_pr_payload(pr_payload, owner, repo)
                result: Dict[str, Any] = {"pull_request": formatted_pr}

                # Логирование созданного Pull Request
                try:
                    pr_data_str = json.dumps(formatted_pr, ensure_ascii=False, indent=2)
                    await logger.info(f"GitHub Pull Request created:\n{pr_data_str}")
                except Exception as e:
                    await logger.warning(f"Failed to log pull request data: {e}")

                rate_limit = self._extract_rate_limit(create_response.headers)
                if rate_limit:
                    result["rate_limit"] = rate_limit

                return {
                    "response": {
                        "ok": True,
                        "result": result
                    }
                }

        except httpx.HTTPError as exc:
            await logger.error(f"GitHub HTTP error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 502,
                    "description": str(exc)
                }
            }
        except Exception as exc:
            await logger.error(f"Unexpected error during GitHub pull request creation: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(exc)}"
                }
            }

    def _simplify_user(self, user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Упрощает объект пользователя GitHub."""
        if not user:
            return None
        return {
            "id": user.get("id"),
            "login": user.get("login"),
            "type": user.get("type"),
            "html_url": user.get("html_url"),
            "avatar_url": user.get("avatar_url")
        }

    def _simplify_label(self, label: Dict[str, Any]) -> Dict[str, Any]:
        """Упрощает объект метки GitHub."""
        return {
            "id": label.get("id"),
            "name": label.get("name"),
            "color": label.get("color"),
            "description": label.get("description")
        }

    def _simplify_milestone(self, milestone: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Упрощает объект milestone GitHub."""
        if not milestone:
            return None
        return {
            "id": milestone.get("id"),
            "title": milestone.get("title"),
            "state": milestone.get("state"),
            "due_on": milestone.get("due_on"),
            "html_url": milestone.get("html_url")
        }

    def _simplify_branch(self, branch: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Упрощает объект ветки GitHub."""
        if not branch:
            return None
        return {
            "label": branch.get("label"),
            "ref": branch.get("ref"),
            "sha": branch.get("sha"),
            "user": self._simplify_user(branch.get("user")),
            "repo": branch.get("repo")
        }

    def _build_pr_payload(self, pr: Dict[str, Any], owner: str, repo: str) -> Dict[str, Any]:
        """Формирует упрощенный объект Pull Request из ответа GitHub API."""
        labels = pr.get("labels") or []
        if isinstance(labels, list):
            label_list = [self._simplify_label(label) for label in labels if isinstance(label, dict)]
        else:
            label_list = []

        assignees_raw = pr.get("assignees") or []
        assignees = [self._simplify_user(assignee) for assignee in assignees_raw if isinstance(assignee, dict)]

        reviewers_raw = pr.get("requested_reviewers") or []
        reviewers = [self._simplify_user(reviewer) for reviewer in reviewers_raw if isinstance(reviewer, dict)]

        return {
            "id": pr.get("id"),
            "node_id": pr.get("node_id"),
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "locked": pr.get("locked"),
            "draft": pr.get("draft"),
            "author": self._simplify_user(pr.get("user")),
            "assignees": assignees,
            "requested_reviewers": reviewers,
            "labels": label_list,
            "milestone": self._simplify_milestone(pr.get("milestone")),
            "body": pr.get("body"),
            "head": self._simplify_branch(pr.get("head")),
            "base": self._simplify_branch(pr.get("base")),
            "url": pr.get("url"),
            "html_url": pr.get("html_url"),
            "diff_url": pr.get("diff_url"),
            "patch_url": pr.get("patch_url"),
            "issue_url": pr.get("issue_url"),
            "commits_url": pr.get("commits_url"),
            "review_comments_url": pr.get("review_comments_url"),
            "review_comment_url": pr.get("review_comment_url"),
            "comments_url": pr.get("comments_url"),
            "statuses_url": pr.get("statuses_url"),
            "repository": {
                "owner": owner,
                "name": repo
            },
            "merged": pr.get("merged"),
            "mergeable": pr.get("mergeable"),
            "rebaseable": pr.get("rebaseable"),
            "mergeable_state": pr.get("mergeable_state"),
            "merged_at": pr.get("merged_at"),
            "merge_commit_sha": pr.get("merge_commit_sha"),
            "comments": pr.get("comments"),
            "review_comments": pr.get("review_comments"),
            "maintainer_can_modify": pr.get("maintainer_can_modify"),
            "commits": pr.get("commits"),
            "additions": pr.get("additions"),
            "deletions": pr.get("deletions"),
            "changed_files": pr.get("changed_files"),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "closed_at": pr.get("closed_at"),
            "author_association": pr.get("author_association")
        }

    def _extract_error_description(self, response: httpx.Response) -> str:
        """Извлекает описание ошибки из ответа GitHub API."""
        try:
            payload = response.json()
        except ValueError:
            return f"GitHub API returned {response.status_code}"

        message = payload.get("message")
        errors = payload.get("errors")
        if errors:
            if isinstance(errors, list):
                joined_errors = "; ".join(
                    error.get("message") if isinstance(error, dict) else str(error)
                    for error in errors[:3]
                )
                if joined_errors:
                    return f"{message}: {joined_errors}" if message else joined_errors
        return message or f"GitHub API returned {response.status_code}"

    def _extract_rate_limit(self, headers: Any) -> Optional[Dict[str, Any]]:
        """Извлекает информацию о rate limit из заголовков ответа."""
        limit = headers.get("X-RateLimit-Limit") if headers else None
        remaining = headers.get("X-RateLimit-Remaining") if headers else None
        reset = headers.get("X-RateLimit-Reset") if headers else None

        if not any([limit, remaining, reset]):
            return None

        def _safe_int(value: Any) -> Optional[int]:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return {
            "limit": _safe_int(limit),
            "remaining": _safe_int(remaining),
            "reset_epoch": _safe_int(reset)
        }


__all__ = ["GitHubCreatePullRequestIntegration"]

