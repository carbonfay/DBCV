"""GitHub Create Pull Request интеграция используя httpx библиотеку."""
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


class GitHubCreatePullRequestIntegration(BaseIntegration):
    """Интеграция для создания Pull Request в GitHub через REST API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_pull_request",
            version="1.0.0",
            name="GitHub Create Pull Request",
            description="Создать Pull Request в репозитории GitHub",
            category="Development",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292f",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title", "head", "base"],
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
                    "title": {
                        "type": "string",
                        "title": "Title",
                        "description": "Заголовок Pull Request"
                    },
                    "head": {
                        "type": "string",
                        "title": "Head",
                        "description": "Ветка-источник (например: feature-branch или user:branch)"
                    },
                    "base": {
                        "type": "string",
                        "title": "Base",
                        "description": "Ветка назначения (например: main)"
                    },
                    "body": {
                        "type": "string",
                        "title": "Body",
                        "description": "Описание Pull Request"
                    },
                    "draft_mode": {
                        "type": "string",
                        "title": "Draft Mode",
                        "description": "Создать Pull Request как черновик (Draft)",
                        "enum": ["no", "yes"],
                        "default": "no"
                    },
                    "maintainer_can_modify_mode": {
                        "type": "string",
                        "title": "Allow maintainers to modify",
                        "description": "Разрешить мейнтейнерам править ветку (актуально для PR из fork)",
                        "enum": ["yes", "no"],
                        "default": "yes"
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
                    "title": "Создать Pull Request",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "title": "Add new feature",
                        "head": "feature-branch",
                        "base": "main",
                        "body": "Описание изменений",
                        "maintainer_can_modify_mode": "yes"
                    }
                },
                {
                    "title": "Создать Draft Pull Request",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "title": "WIP: feature",
                        "head": "feature-branch",
                        "base": "main",
                        "draft_mode": "yes",
                        "maintainer_can_modify_mode": "yes"
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

        # --- обязательные параметры ---
        owner = config.get("owner")
        repo = config.get("repo")
        title = config.get("title")
        head = config.get("head")
        base = config.get("base")

        if not owner or not repo or not title or not head or not base:
            await logger.error("owner, repo, title, head and base are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo, title, head and base are required"
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

        cred_payload = creds.get("payload", {}) or creds
        token = (
            cred_payload.get("api_key")
            or cred_payload.get("token")
            or cred_payload.get("access_token")
            or cred_payload.get("github_token")
            or cred_payload.get("pat")
        )

        if not token:
            await logger.error(
                f"GitHub token not found in credentials. Available keys: {list(cred_payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }

        url = f"{base_url}/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "DBCV-GitHubCreatePullRequestIntegration/1.0.0"
        }

        # --- payload для POST /pulls ---
        payload: Dict[str, Any] = {
            "title": title,
            "head": head,
            "base": base
        }

        if "body" in config:
            payload["body"] = config.get("body")

        draft_mode = config.get("draft_mode", "no")
        if draft_mode == "yes":
            payload["draft"] = True

        mcm_mode = config.get("maintainer_can_modify_mode", "yes")
        payload["maintainer_can_modify"] = True if mcm_mode == "yes" else False

        try:
            async with httpx.AsyncClient(timeout=float(timeout_seconds)) as client:
                resp = await client.post(url, json=payload, headers=headers)

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
