"""GitHub Create Issue интеграция используя httpx библиотеку.

Документация API: https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#create-an-issue
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


class GitHubCreateIssueIntegration(BaseIntegration):
    """Интеграция для создания Issue в репозитории GitHub"""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_issue",
            version="1.0.0",
            name="GitHub Create Issue",
            description="Создать issue в репозитории GitHub",
            category="developer_tools",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title"],
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
                        "description": "Заголовок issue"
                    },
                    "body": {
                        "type": "string",
                        "title": "Body",
                        "description": "Тело issue (описание)"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "labels": {
                        "type": "array",
                        "title": "Labels",
                        "items": {"type": "string"}
                    },
                    
                }
            },
            credentials_provider="github",
            credentials_strategy="api_key",
            library_name="httpx>=0.25.0" if HTTPX_AVAILABLE else None,
            examples=[
            {
                "title": "Create simple issue",
                "config": {
                "owner": "octocat",
                "repo": "hello-world",
                "title": "Issue from DBCV",
                "body": "This issue was created by DBCV integration"
                }
            },
            {
                "title": "Create issue with labels and assignees",
                "config": {
                "owner": "octocat",
                "repo": "hello-world",
                "title": "Bug: Something broken",
                "body": "Steps to reproduce...",
                "labels": ["bug", "high-priority"],
                "assignees": ["octocat"]
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
        """Создает issue в указанном репозитории.

        Ожидает в `config`: `owner`, `repo`, `title` и опционально `body`, `labels`, `assignees`.

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
        title = config.get("title")
        body = config.get("body")
        labels = config.get("labels")
        assignees = config.get("assignees")

        if not owner or not repo or not title:
            await logger.error("owner, repo and title are required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo and title are required in config"
                }
            }

        url = f"https://api.github.com/repos/{owner}/{repo}/issues"

        payload_json: Dict[str, Any] = {"title": str(title)}
        if body is not None:
            payload_json["body"] = str(body)
        if labels is not None:
            payload_json["labels"] = labels
        if assignees is not None:
            payload_json["assignees"] = assignees
        
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        try:
            # Log headers and body to console for debugging
            try:
                import json as _json
                pretty_body = _json.dumps(payload_json, ensure_ascii=False)
            except Exception:
                pretty_body = str(payload_json)

            print(f"GitHub Create Issue - URL: {url}")
            print("Headers:", headers)
            print("Request body:", pretty_body)

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload_json, headers=headers)

            # Успешное создание возвращает 201 Created
            if 200 <= resp.status_code < 300:
                try:
                    result_json = resp.json()
                except Exception:
                    result_json = {"status_code": resp.status_code, "text": resp.text}

                return {"response": {"ok": True, "result": result_json}}

            # Ошибки от GitHub
            await logger.error(f"GitHub API error: {resp.status_code} - {resp.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": resp.status_code,
                    "description": resp.text
                }
            }

        except httpx.HTTPError as e:
            await logger.error(f"HTTPX error while creating GitHub issue: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while creating GitHub issue: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
