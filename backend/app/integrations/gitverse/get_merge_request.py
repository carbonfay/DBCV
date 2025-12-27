"""GitVerse Create Merge Request — создаёт merge request (pull request) через GitVerse REST API (GitHub-compatible)."""
from typing import Dict, Any, Optional
from uuid import UUID
from urllib.parse import quote

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx напрямую
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False


class GitVerseCreateMergeRequestIntegration(BaseIntegration):
    """Интеграция для создания merge request в GitVerse (GitHub-like Pulls API)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="gitverse_create_merge_request",
            version="1.0.0",
            name="GitVerse Create Merge Request",
            description="Create a merge request (pull request) in a GitVerse repository via REST API",
            category="developer",
            icon_s3_key="icons/integrations/gitverse.svg",
            color="#2b6cb0",
            config_schema={
                "type": "object",
                "required": ["repo", "title", "head", "base"],
                "properties": {
                    "api_url": {
                        "type": "string",
                        "title": "API Base URL",
                        "description": "Base API URL for GitVerse (default: https://api.gitverse.ru)"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository (owner/repo)",
                        "description": "Repository path in form owner/repo"
                    },
                    "title": {"type": "string", "title": "Merge Request Title"},
                    "head": {"type": "string", "title": "Head Branch or Commit"},
                    "base": {"type": "string", "title": "Base Branch"},
                    "body": {"type": "string", "title": "Description"}
                }
            },
            credentials_provider="gitverse",
            credentials_strategy="api_key",
            library_name="httpx>=0.18.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Create merge request",
                    "config": {
                        "api_url": "https://api.gitverse.ru",
                        "repo": "namespace/project",
                        "title": "Feature: add API",
                        "head": "feature/api",
                        "base": "main",
                        "body": "Please review changes"
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

        # Сначала gitverse/api_key, затем fallback other/api_key
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="gitverse",
            strategy="api_key"
        ) or await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
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

        api_url: Optional[str] = config.get("api_url") or "https://api.gitverse.ru"
        repo: Optional[str] = config.get("repo")
        title: Optional[str] = config.get("title")
        head: Optional[str] = config.get("head")
        base: Optional[str] = config.get("base")
        body = config.get("body")

        if not repo or not title or not head or not base:
            await logger.error("repo, title, head, base are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "repo, title, head, base are required"
                }
            }

        def _encode_part(part: str) -> str:
            return quote(str(part).strip(), safe="")

        if "/" in repo:
            owner, _, name = repo.partition("/")
            repo_path = f"{_encode_part(owner)}/{_encode_part(name)}"
        else:
            repo_path = _encode_part(repo)

        base_api = api_url.rstrip("/")
        endpoint = f"{base_api}/repos/{repo_path}/pulls"

        headers = {
            "Accept": "application/vnd.gitverse.object+json;version=1",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        json_data = {
            "title": title,
            "head": head,
            "base": base,
        }
        if body:
            json_data["body"] = body

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(endpoint, headers=headers, json=json_data, timeout=10.0)

            try:
                resp_json = resp.json()
            except Exception:
                resp_json = {"text": resp.text}

            if 200 <= resp.status_code < 300:
                return {"response": {"ok": True, "result": resp_json}}

            snippet = (resp.text or "")[:300]
            await logger.error(f"GitVerse API returned {resp.status_code} for {endpoint}: {snippet}")
            return {
                "response": {
                    "ok": False,
                    "error_code": resp.status_code,
                    "description": resp_json
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while creating merge request for {endpoint}: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
