"""GitHub Create Issue интеграция используя httpx для GitHub REST API."""
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


class GithubCreateIssueIntegration(BaseIntegration):
    """Интеграция для создания issue в репозитории GitHub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_issue",
            version="1.0.0",
            name="GitHub Create Issue",
            description="Создание issue в репозитории GitHub через REST API",
            category="version_control",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title"],
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
                    "title": {
                        "type": "string",
                        "title": "Title",
                        "description": "Заголовок issue (можно использовать переменные: {$session.issue_title$})"
                    },
                    "body": {
                        "type": "string",
                        "title": "Body",
                        "description": "Текст issue"
                    },
                    "labels": {
                        "type": "array",
                        "title": "Labels",
                        "description": "Список меток, например: [\"bug\", \"urgent\"]",
                        "items": {"type": "string"}
                    },
                    "assignees": {
                        "type": "array",
                        "title": "Assignees",
                        "description": "Список логинов исполнителей, например: [\"username\"]",
                        "items": {"type": "string"}
                    }
                }
            },
            credentials_provider="github",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Простое issue",
                    "config": {
                        "owner": "octocat",
                        "repo": "Hello-World",
                        "title": "Found a bug"
                    }
                },
                {
                    "title": "Issue с меткой и исполнителем",
                    "config": {
                        "owner": "octocat",
                        "repo": "Hello-World",
                        "title": "Bug report",
                        "body": "Steps to reproduce...",
                        "labels": ["bug"],
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
        title = config.get("title")
        body = config.get("body")
        labels = config.get("labels", [])
        assignees = config.get("assignees", [])

        if not owner or not repo or not title:
            await logger.error("owner, repo and title are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo and title are required"
                }
            }

        # Собираем тело запроса (передаём только заданные поля)
        issue_data = {"title": str(title)}
        if body:
            issue_data["body"] = str(body)
        if labels:
            issue_data["labels"] = [str(label) for label in labels]
        if assignees:
            issue_data["assignees"] = [str(a) for a in assignees]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues",
                    headers=headers,
                    json=issue_data
                )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", response.text)
                    # GitHub в случае 422 отдаёт детали в массиве errors
                    error_details = error_data.get("errors")
                    if error_details:
                        details = "; ".join(
                            f"{err.get('field', 'unknown')}: {err.get('message') or err.get('code')}"
                            for err in error_details
                        )
                        error_message = f"{error_message} [{details}]"
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

            issue = response.json()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": issue.get("id"),
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "state": issue.get("state"),
                        "html_url": issue.get("html_url"),
                        "created_at": issue.get("created_at"),
                        "user": issue.get("user", {}).get("login") if issue.get("user") else None
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
