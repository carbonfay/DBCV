"""GitHub Get Issue интеграция используя httpx библиотеку."""
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


class GitHubGetIssueIntegration(BaseIntegration):
    """Интеграция для получения issue из GitHub через GitHub REST API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_issue",
            version="1.0.0",
            name="GitHub Get Issue",
            description="Получить issue по номеру из репозитория GitHub через REST API",
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
                        "description": "Логин пользователя или организации (владелец репозитория)"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Название репозитория"
                    },
                    "issue_number": {
                        "type": "integer",
                        "title": "Issue Number",
                        "description": "Номер issue в репозитории",
                        "minimum": 1
                    },
                    "base_url": {
                        "type": "string",
                        "title": "GitHub API Base URL",
                        "description": "Базовый URL GitHub API (обычно не нужно менять)",
                        "default": "https://api.github.com"
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "title": "Timeout (seconds)",
                        "description": "Таймаут HTTP запроса",
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
                    "title": "Получить issue по номеру",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "issue_number": 1
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
        Выполняет интеграцию используя библиотеку httpx.
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        Returns:
            Результат выполнения в формате системы
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

        # Валидация config
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
            issue_number_int = int(issue_number)
            if issue_number_int < 1:
                raise ValueError("issue_number must be >= 1")
        except Exception:
            await logger.error("issue_number must be a positive integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "issue_number must be a positive integer"
                }
            }

        base_url = (config.get("base_url") or "https://api.github.com").rstrip("/")
        timeout_seconds = config.get("timeout_seconds") or 20

        # Получаем credentials
        await logger.info(f"Resolve creds: bot_id={bot_id}, provider=other, strategy=api_key")
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        await logger.info(f"Resolved creds is None? {creds is None}. Keys: {list(creds.keys()) if creds else None}")

        if not creds:
            await logger.error("GitHub credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            payload = creds  # fallback

        # Поддержим несколько распространённых ключей
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

        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number_int}"

        headers = {
            # GitHub принимает PAT как "token <PAT>" (классика) и Bearer для некоторых типов токенов.
            # Используем token как наиболее совместимый вариант.
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "DBCV-GitHubGetIssueIntegration/1.0.0"
        }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ
        try:
            async with httpx.AsyncClient(timeout=float(timeout_seconds)) as client:
                resp = await client.get(url, headers=headers)

            if resp.status_code >= 400:
                # GitHub обычно возвращает JSON с message / documentation_url
                try:
                    err_json = resp.json()
                except Exception:
                    err_json = {"raw": resp.text}

                await logger.error(f"GitHub API error {resp.status_code}: {err_json}")

                # Нормализуем error_code под HTTP
                return {
                    "response": {
                        "ok": False,
                        "error_code": resp.status_code,
                        "description": err_json.get("message") if isinstance(err_json, dict) else str(err_json)
                    }
                }

            data = resp.json()

            # Возвращаем результат в формате системы
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
            # DNS/TLS/connection errors etc.
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
