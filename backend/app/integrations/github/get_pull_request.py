"""GitHub Get Pull Request интеграция используя httpx для GitHub REST API."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


GITHUB_API_URL = "https://api.github.com"


class GithubGetPullRequestIntegration(BaseIntegration):
    """Интеграция для получения pull request из репозитория GitHub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_pull_request",
            version="1.0.0",
            name="GitHub Get Pull Request",
            description="Получение pull request из репозитория GitHub через REST API",
            category="version_control",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "pull_number"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Owner",
                        "description": "Владелец репозитория (логин пользователя или организации)"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Название репозитория"
                    },
                    "pull_number": {
                        "type": "string",
                        "title": "Pull Request Number",
                        "description": "Номер pull request (число или переменная: {$session.pull_number$})"
                    }
                }
            },
            credentials_provider="github",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Получение pull request",
                    "config": {
                        "owner": "octocat",
                        "repo": "Hello-World",
                        "pull_number": "42"
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
        Выполняет интеграцию используя httpx для запроса к GitHub REST API.

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

        # Получаем access_token из credentials
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
                    "description": "GitHub access_token not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        access_token = payload.get("access_token") or payload.get("token")
        if not access_token:
            await logger.error(f"access_token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "access_token not found in credentials"
                }
            }

        # Получаем параметры из config
        owner = config.get("owner")
        repo = config.get("repo")
        pull_number = config.get("pull_number")

        if not owner or not repo or not pull_number:
            await logger.error("owner, repo and pull_number are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo and pull_number are required"
                }
            }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{int(pull_number)}",
                    headers=headers
                )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", response.text)
                except Exception:
                    error_message = response.text
                await logger.error(f"GitHub API error: {error_message}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": error_message
                    }
                }

            pull_request = response.json()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": pull_request.get("id"),
                        "number": pull_request.get("number"),
                        "title": pull_request.get("title"),
                        "state": pull_request.get("state"),
                        "html_url": pull_request.get("html_url"),
                        "created_at": pull_request.get("created_at"),
                        "merged_at": pull_request.get("merged_at"),
                        "user": pull_request.get("user", {}).get("login") if pull_request.get("user") else None,
                        "head": {
                            "ref": pull_request.get("head", {}).get("ref"),
                            "sha": pull_request.get("head", {}).get("sha")
                        } if pull_request.get("head") else None,
                        "base": {
                            "ref": pull_request.get("base", {}).get("ref"),
                            "sha": pull_request.get("base", {}).get("sha")
                        } if pull_request.get("base") else None
                    }
                }
            }
        except httpx.HTTPError as e:
            await logger.error(f"GitHub HTTP error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
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
