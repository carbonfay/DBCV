"""GitVerse Create Issue интеграция — создаёт issue через REST API (GitHub-like).
Использует `httpx` для выполнения HTTP-запросов.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


# Попытка импортировать httpx (должен присутствовать в requirements.txt)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False


class GitVerseCreateIssueIntegration(BaseIntegration):
    """Интеграция для создания issue в GitVerse/GitHub-подобных репозиториях."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="gitverse_create_issue",
            version="1.0.0",
            name="GitVerse Create Issue",
            description="Create an issue in a Git repository via REST API (GitHub-like)",
            category="developer",
            icon_s3_key="icons/integrations/gitverse.svg",
            color="#2b6cb0",
            config_schema={
                "type": "object",
                "required": ["api_url", "repo", "title"],
                "properties": {
                    "api_url": {
                        "type": "string",
                        "title": "API Base URL",
                        "description": "Base API URL, e.g. https://api.github.com"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Repository in format owner/repo"
                    },
                    "title": {"type": "string", "title": "Issue Title"},
                    "body": {"type": "string", "title": "Issue Body"},
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "assignees": {"type": "array", "items": {"type": "string"}}
                }
            },
            credentials_provider="gitverse",
            credentials_strategy="api_key",
            library_name="httpx>=0.18.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Create simple issue",
                    "config": {
                        "api_url": "https://api.github.com",
                        "repo": "owner/repo",
                        "title": "Bug: something is broken",
                        "body": "Steps to reproduce..."
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
            provider="gitverse",
            strategy="api_key"
        )

        if not creds:
            await logger.error("GitVerse credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key not found in credentials"
                }
            }

        payload = creds.get("payload", {}) if isinstance(creds, dict) else creds
        if not payload:
            payload = creds

        api_key = payload.get("api_key") or payload.get("token") or payload.get("access_token")
        if not api_key:
            await logger.error("API key not found in credentials payload")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key/token/access_token not found in credentials"
                }
            }

        # Параметры конфигурации
        api_url: Optional[str] = config.get("api_url")
        repo: Optional[str] = config.get("repo")
        title: Optional[str] = config.get("title")
        body: Optional[str] = config.get("body")
        labels = config.get("labels")
        assignees = config.get("assignees")

        if not api_url or not repo or not title:
            await logger.error("api_url, repo and title are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "api_url, repo and title are required"
                }
            }

        # Формируем endpoint (GitHub-like)
        endpoint = f"{api_url.rstrip('/')}/repos/{repo}/issues"

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {api_key}"
        }

        json_body = {"title": title}
        if body:
            json_body["body"] = body
        if labels:
            json_body["labels"] = labels
        if assignees:
            json_body["assignees"] = assignees

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(endpoint, json=json_body, headers=headers, timeout=10.0)

            try:
                resp_json = resp.json()
            except Exception:
                resp_json = {"text": resp.text}

            if 200 <= resp.status_code < 300:
                return {"response": {"ok": True, "result": resp_json}}
            else:
                await logger.error(f"GitVerse API returned {resp.status_code}: {resp.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": resp.status_code,
                        "description": resp_json
                    }
                }

        except Exception as e:
            await logger.error(f"Unexpected error while creating issue: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
