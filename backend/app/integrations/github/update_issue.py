"""GitHub Update Issue интеграция используя httpx библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку в backend код
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore


class GitHubUpdateIssueIntegration(BaseIntegration):
    """Интеграция для обновления issue в GitHub через REST API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_update_issue",
            version="1.0.0",
            name="GitHub Update Issue",
            description="Обновить issue (title, body, state и др.) в репозитории GitHub",
            category="Development",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292f",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "issue_number"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Owner",
                        "description": "Логин пользователя или организации"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Название репозитория"
                    },
                    "issue_number": {
                        "type": "integer",
                        "title": "Issue Number",
                        "description": "Номер issue",
                        "minimum": 1
                    },
                    "title": {
                        "type": "string",
                        "title": "Title",
                        "description": "Новый заголовок issue"
                    },
                    "body": {
                        "type": "string",
                        "title": "Body",
                        "description": "Новое описание issue"
                    },
                    "state": {
                        "type": "string",
                        "title": "State",
                        "enum": ["open", "closed"],
                        "description": "Состояние issue"
                    },
                    "labels": {
                        "type": "array",
                        "title": "Labels",
                        "description": "Список label-ов",
                        "items": {
                            "type": "string"
                        }
                    },
                    "assignees": {
                        "type": "array",
                        "title": "Assignees",
                        "description": "Список логинов пользователей",
                        "items": {
                            "type": "string"
                        }
                    },
                    "milestone": {
                        "type": ["integer", "null"],
                        "title": "Milestone",
                        "description": "ID milestone или null"
                    },
                    "base_url": {
                        "type": "string",
                        "title": "GitHub API Base URL",
                        "default": "https://api.github.com"
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "title": "Timeout (seconds)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 120
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Обновить заголовок и описание issue",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "issue_number": 1,
                        "title": "Updated title",
                        "body": "Updated issue description"
                    }
                },
                {
                    "title": "Закрыть issue",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "issue_number": 1,
                        "state": "closed"
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
        """Выполняет обновление issue через GitHub API."""
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        # --- обязательные параметры ---
        owner = config.get("owner")
        repo = config.get("repo")
        issue_number = config.get("issue_number")

        if not owner or not repo or not issue_number:
            await logger.error("owner, repo and issue_number are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo and issue_number are required"
                }
            }

        try:
            issue_number = int(issue_number)
            if issue_number < 1:
                raise ValueError
        except Exception:
            await logger.error("issue_number must be a positive integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "issue_number must be a positive integer"
                }
            }

        # --- формируем payload для PATCH ---
        update_payload: Dict[str, Any] = {}
        for field in ("title", "body", "state", "labels", "assignees", "milestone"):
            if field in config:
                update_payload[field] = config.get(field)

        if not update_payload:
            await logger.error("No fields provided to update issue")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "At least one field must be provided to update issue"
                }
            }

        base_url = (config.get("base_url") or "https://api.github.com").rstrip("/")
        timeout_seconds = config.get("timeout_seconds") or 20

        # --- credentials ---
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
                    "description": "GitHub token not found in credentials"
                }
            }

        payload = creds.get("payload", {}) or creds
        token = (
            payload.get("api_key")
            or payload.get("token")
            or payload.get("access_token")
            or payload.get("github_token")
            or payload.get("pat")
        )

        if not token:
            await logger.error(f"GitHub token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }

        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "DBCV-GitHubUpdateIssueIntegration/1.0.0"
        }

        try:
            async with httpx.AsyncClient(timeout=float(timeout_seconds)) as client:
                resp = await client.patch(url, json=update_payload, headers=headers)

            if resp.status_code >= 400:
                try:
                    err_json = resp.json()
                except Exception:
                    err_json = {"raw": resp.text}

                await logger.error(f"GitHub API error {resp.status_code}: {err_json}")

                return {
                    "response": {
                        "ok": False,
                        "error_code": resp.status_code,
                        "description": err_json.get("message") if isinstance(err_json, dict) else str(err_json)
                    }
                }

            data = resp.json()

            return {
                "response": {
                    "ok": True,
                    "result": data
                }
            }

        except httpx.TimeoutException as e:
            await logger.error(f"GitHub request timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": str(e)
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"GitHub request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 502,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
