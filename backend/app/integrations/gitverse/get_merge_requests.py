"""GitVerse Get Merge Requests — получает список merge requests через GitVerse REST API (GitHub-compatible)."""
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


class GitVerseGetMergeRequestsIntegration(BaseIntegration):
    """Интеграция для получения списка merge requests из GitVerse (GitHub-compatible API)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="gitverse_get_merge_requests",
            version="1.0.0",
            name="GitVerse Get Merge Requests",
            description="Fetch merge requests from a GitVerse repository via REST API",
            category="developer",
            icon_s3_key="icons/integrations/gitverse.svg",
            color="#2b6cb0",
            config_schema={
                "type": "object",
                "required": ["repo"],
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
                    "state": {
                        "type": "string",
                        "title": "State",
                        "description": "Filter by state (e.g. open, closed, all)",
                        "default": None
                    },
                    "page": {
                        "type": "integer",
                        "title": "Page",
                        "default": 1,
                        "minimum": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "title": "Per Page",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            },
            credentials_provider="gitverse",
            credentials_strategy="api_key",
            library_name="httpx>=0.18.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Get open merge requests",
                    "config": {
                        "api_url": "https://api.gitverse.ru",
                        "repo": "namespace/project",
                        "state": "open",
                        "page": 1,
                        "per_page": 10
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

        # Сначала провайдер gitverse/api_key, затем fallback other/api_key
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
        state: Optional[str] = config.get("state")
        page = config.get("page") or 1
        per_page = config.get("per_page") or 10

        if not repo:
            await logger.error("repo is required (owner/repo)")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "repo is required (owner/repo)"
                }
            }

        def _encode_part(part: str) -> str:
            return quote(str(part).strip(), safe="")

        if "/" in repo:
            owner, _, name = repo.partition("/")
            repo_path = f"{_encode_part(owner)}/{_encode_part(name)}"
        else:
            repo_path = _encode_part(repo)

        base = api_url.rstrip("/")
        endpoint = f"{base}/repos/{repo_path}/issues"

        headers = {
            "Accept": "application/vnd.gitverse.object+json;version=1",
            "Authorization": f"Bearer {api_key}",
        }

        params = {
            "state": state,
            "page": page,
            "per_page": per_page,
        }

        params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(endpoint, headers=headers, params=params, timeout=10.0)

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
            await logger.error(f"Unexpected error while fetching merge requests from {endpoint}: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
