"""GitHub Create Pull Request интеграция используя httpx библиотеку.

Документация API: https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку на прямую
try:
    import httpx  # type: ignore
    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False


class GitHubCreatePullRequestIntegration(BaseIntegration):
    """Интеграция для создания Pull Request в репозитории GitHub"""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_pr",
            version="1.0.0",
            name="GitHub Create Pull Request",
            description="Создать pull request в репозитории GitHub",
            category="developer_tools",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title", "head", "base"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Owner",
                        "description": "Владелец репозитория (имя пользователя или организация)"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Название репозитория"
                    },
                    "title": {
                        "type": "string",
                        "title": "Title",
                        "description": "Заголовок pull request"
                    },
                    "head": {
                        "type": "string",
                        "title": "Head",
                        "description": "Имя ветки с вашими изменениями (например, feature-branch)"
                    },
                    "base": {
                        "type": "string",
                        "title": "Base",
                        "description": "Целевая ветка для слияния (например, main)"
                    },
                    "body": {
                        "type": "string",
                        "title": "Body",
                        "description": "Описание pull request"
                    },
                    "issue": {
                        "type": "integer",
                        "title": "Issue",
                        "description": "Номер issue (опционально) для создания PR из issue"
                    },
                    "draft": {
                        "type": "string",
                        "title": "Draft",
                        "description": "Создать как draft pull request"
                    },
                    "maintainer_can_modify": {
                        "type": "string",
                        "title": "Maintainer Can Modify",
                        "description": "Разрешить мейнтейнерам репозитория вносить изменения"
                    }
                }
            },
            credentials_provider="github",
            credentials_strategy="api_key",
            library_name="httpx>=0.25.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Create simple pull request",
                    "config": {
                        "owner": "octocat",
                        "repo": "hello-world",
                        "head": "feature-branch",
                        "base": "main",
                        "title": "Add new feature",
                        "body": "This PR introduces a new feature."
                    }
                },
                {
                    "title": "Create draft pull request",
                    "config": {
                        "owner": "octocat",
                        "repo": "hello-world",
                        "head": "wip-branch",
                        "base": "develop",
                        "title": "WIP: work in progress",
                        "draft": True
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Создает pull request в указанном репозитории.

        Ожидает в `config`: `owner`, `repo`, `head`, `base`, `title` и опционально `body`, `draft`, `maintainer_can_modify`.

        Credentials должны быть доступны через `credentials_resolver.get_default_for` и содержать
        в `payload` ключ с токеном: `token` или `access_token` или `personal_access_token`.
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="github",
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

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds

        token = None
        if isinstance(payload, dict):
            token = payload.get("token") or payload.get("access_token") or payload.get("personal_access_token")

        if not token:
            await logger.error("GitHub token not found in credentials payload")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }

        owner = config.get("owner")
        repo = config.get("repo")
        head = config.get("head")
        base = config.get("base")
        title = config.get("title")
        issue = config.get("issue")
        body = config.get("body")
        draft = config.get("draft")
        maintainer_can_modify = config.get("maintainer_can_modify")

        if not owner or not repo or not head or not base or not title:
            await logger.error("owner, repo, head, base and title are required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo, head, base and title are required in config"
                }
            }

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

        payload_json: Dict[str, Any] = {"title": str(title), "head": str(head), "base": str(base)}
        if body is not None:
            payload_json["body"] = str(body)
        if issue is not None:
            try:
                payload_json["issue"] = int(issue)
            except Exception:
                payload_json["issue"] = None
        def _convert_to_bool_or_str(v: Any) -> Any:
            if isinstance(v, bool):
                return v
            s = str(v).strip()
            lower = s.lower()
            if lower in ("true", "1", "yes", "y", "on"):
                return True
            if lower in ("false", "0", "no", "n", "off"):
                return False
            try:
                return bool(int(s))
            except Exception:
                return s

        if draft is not None:
            payload_json["draft"] = _convert_to_bool_or_str(draft)
        if maintainer_can_modify is not None:
            payload_json["maintainer_can_modify"] = _convert_to_bool_or_str(maintainer_can_modify)

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        try:
            # Try to pretty-print payload for debugging
            try:
                import json as _json
                pretty_body = _json.dumps(payload_json, ensure_ascii=False)
            except Exception:
                pretty_body = str(payload_json)

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload_json, headers=headers)

            if 200 <= resp.status_code < 300:
                try:
                    result_json = resp.json()
                except Exception:
                    result_json = {"status_code": resp.status_code, "text": resp.text}

                return {"response": {"ok": True, "result": result_json}}

            await logger.error(f"GitHub API error: {resp.status_code} - {resp.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": resp.status_code,
                    "description": resp.text
                }
            }

        except httpx.HTTPError as e:
            await logger.error(f"HTTPX error while creating GitHub pull request: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while creating GitHub pull request: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
