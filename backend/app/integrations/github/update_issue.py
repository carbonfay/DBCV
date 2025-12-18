"""GitHub Update Issue интеграция с использованием httpx."""
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


class GitHubUpdateIssueIntegration(BaseIntegration):
    """Интеграция для обновления Issue в GitHub."""

    _GITHUB_API_URL = "https://api.github.com"

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_update_issue",
            version="1.0.0",
            name="GitHub Update Issue",
            description="Обновление Issue в GitHub через REST API.",
            category="github",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292E",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "issue_number"],
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
                    "issue_number": {
                        "type": "string",
                        "title": "Issue Number",
                        "description": "Номер Issue (можно передать числом или строкой)."
                    },
                    "title": {
                        "type": "string",
                        "title": "Issue Title",
                        "description": "Новый заголовок Issue (опционально)."
                    },
                    "body": {
                        "type": "string",
                        "title": "Issue Body",
                        "description": "Новое содержимое Issue (опционально)."
                    },
                    "state": {
                        "type": "string",
                        "title": "Issue State",
                        "description": "Состояние Issue: 'open' или 'closed' (опционально).",
                        "enum": ["open", "closed"]
                    },
                    "state_reason": {
                        "type": "string",
                        "title": "State Reason",
                        "description": "Причина изменения состояния: 'completed', 'not_planned', 'reopened' (опционально).",
                        "enum": ["completed", "not_planned", "reopened"]
                    },
                    "labels": {
                        "type": "array",
                        "title": "Labels",
                        "description": "Список меток Issue (опционально).",
                        "items": {
                            "type": "string"
                        }
                    },
                    "assignees": {
                        "type": "array",
                        "title": "Assignees",
                        "description": "Список логинов пользователей для назначения на Issue (опционально).",
                        "items": {
                            "type": "string"
                        }
                    },
                    "milestone": {
                        "type": ["integer", "null"],
                        "title": "Milestone",
                        "description": "ID milestone или null для удаления (опционально)."
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Обновить заголовок Issue",
                    "config": {
                        "owner": "barsux",
                        "repo": "barsux",
                        "issue_number": 1347,
                        "title": "Новый заголовок Issue"
                    }
                },
                {
                    "title": "Закрыть Issue",
                    "config": {
                        "owner": "barsux",
                        "repo": "barsux",
                        "issue_number": 1347,
                        "state": "closed",
                        "state_reason": "completed"
                    }
                },
                {
                    "title": "Обновить метки и назначить исполнителей",
                    "config": {
                        "owner": "barsux",
                        "repo": "barsux",
                        "issue_number": 1347,
                        "labels": ["bug", "urgent"],
                        "assignees": ["barsux"]
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
        Обновляет Issue в GitHub.

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
            issue_number_raw = config.get("issue_number")
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

        issue_number = self._parse_issue_number(issue_number_raw)
        if issue_number is None:
            await logger.error("issue_number must be an integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "issue_number must be an integer"
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

        # Формируем тело запроса для обновления Issue
        update_payload: Dict[str, Any] = {}
        
        if "title" in config:
            title = config.get("title")
            if title is not None:
                update_payload["title"] = str(title).strip()
        
        if "body" in config:
            body = config.get("body")
            if body is not None:
                update_payload["body"] = str(body)
        
        if "state" in config:
            state = config.get("state")
            if state is not None:
                state_str = str(state).strip().lower()
                if state_str in ["open", "closed"]:
                    update_payload["state"] = state_str
                else:
                    await logger.error(f"Invalid state value: {state}. Must be 'open' or 'closed'")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "state must be 'open' or 'closed'"
                        }
                    }
        
        if "state_reason" in config:
            state_reason = config.get("state_reason")
            if state_reason is not None:
                state_reason_str = str(state_reason).strip().lower()
                if state_reason_str in ["completed", "not_planned", "reopened"]:
                    update_payload["state_reason"] = state_reason_str
                else:
                    await logger.error(f"Invalid state_reason value: {state_reason}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "state_reason must be 'completed', 'not_planned', or 'reopened'"
                        }
                    }
        
        if "labels" in config:
            labels = config.get("labels")
            if labels is not None:
                if isinstance(labels, list):
                    update_payload["labels"] = [str(label).strip() for label in labels if label]
                else:
                    await logger.error("labels must be a list")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "labels must be a list"
                        }
                    }
        
        if "assignees" in config:
            assignees = config.get("assignees")
            if assignees is not None:
                if isinstance(assignees, list):
                    update_payload["assignees"] = [str(assignee).strip() for assignee in assignees if assignee]
                else:
                    await logger.error("assignees must be a list")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "assignees must be a list"
                        }
                    }
        
        if "milestone" in config:
            milestone = config.get("milestone")
            if milestone is not None:
                if milestone is None or milestone == "":
                    update_payload["milestone"] = None
                else:
                    try:
                        milestone_id = int(milestone)
                        update_payload["milestone"] = milestone_id
                    except (TypeError, ValueError):
                        await logger.error("milestone must be an integer or null")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 400,
                                "description": "milestone must be an integer or null"
                            }
                        }

        if not update_payload:
            await logger.error("At least one field must be provided for update")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "At least one field must be provided for update (title, body, state, labels, assignees, milestone)"
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
                update_response = await client.patch(
                    f"/repos/{owner}/{repo}/issues/{issue_number}",
                    headers=headers,
                    json=update_payload
                )

                if update_response.status_code >= 400:
                    error_description = self._extract_error_description(update_response)
                    await logger.error(f"GitHub API error {update_response.status_code}: {error_description}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": update_response.status_code,
                            "description": error_description
                        }
                    }

                try:
                    issue_payload = update_response.json()
                except ValueError:
                    await logger.error("Unable to parse GitHub issue response as JSON")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": "Unable to parse GitHub issue response"
                        }
                    }

                formatted_issue = self._build_issue_payload(issue_payload, owner, repo)
                result: Dict[str, Any] = {"issue": formatted_issue}

                rate_limit = self._extract_rate_limit(update_response.headers)
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
            await logger.error(f"Unexpected error during GitHub issue update: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(exc)}"
                }
            }

    def _parse_issue_number(self, value: Any) -> Optional[int]:
        """Преобразует номер issue в int."""
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
        return number if number > 0 else None

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

    def _build_issue_payload(self, issue: Dict[str, Any], owner: str, repo: str) -> Dict[str, Any]:
        """Формирует упрощенный объект Issue из ответа GitHub API."""
        labels = issue.get("labels") or []
        if isinstance(labels, list):
            label_list = [self._simplify_label(label) for label in labels if isinstance(label, dict)]
        else:
            label_list = []

        assignees_raw = issue.get("assignees") or []
        assignees = [self._simplify_user(assignee) for assignee in assignees_raw if isinstance(assignee, dict)]

        return {
            "id": issue.get("id"),
            "node_id": issue.get("node_id"),
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "state_reason": issue.get("state_reason"),
            "locked": issue.get("locked"),
            "author": self._simplify_user(issue.get("user")),
            "assignees": assignees,
            "labels": label_list,
            "milestone": self._simplify_milestone(issue.get("milestone")),
            "body": issue.get("body"),
            "body_text": issue.get("body_text"),
            "url": issue.get("url"),
            "html_url": issue.get("html_url"),
            "repository": {
                "owner": owner,
                "name": repo
            },
            "comments_total": issue.get("comments"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "closed_at": issue.get("closed_at"),
            "is_pull_request": bool(issue.get("pull_request")),
            "reactions": issue.get("reactions") or {},
            "timeline_url": issue.get("timeline_url"),
            "draft": issue.get("draft"),
            "author_association": issue.get("author_association")
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


__all__ = ["GitHubUpdateIssueIntegration"]

