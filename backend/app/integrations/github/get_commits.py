"""GitHub Get Commits интеграция используя библиотеку aiohttp."""
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from aiohttp import ClientSession


class GitHubGetCommitsIntegration(BaseIntegration):
    """Интеграция для получения списка коммитов из GitHub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_commits",
            version="1.0.0",
            name="GitHub Get Commits",
            description="Получение списка коммитов из репозитория GitHub через API",
            category="version_control",
            icon_s3_key="icons/integrations/github.svg",
            color="#181717",
            config_schema={
                "type": "object",
                "required": ["repository"],
                "properties": {
                    "repository": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Полное имя репозитория (например, owner/repo)"
                    },
                    "branch": {
                        "type": "string",
                        "title": "Branch",
                        "description": "Имя ветки (по умолчанию: main)",
                        "default": "main"
                    },
                    "per_page": {
                        "type": "integer",
                        "title": "Per Page",
                        "description": "Количество коммитов на странице (максимум 100)",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "page": {
                        "type": "integer",
                        "title": "Page",
                        "description": "Номер страницы",
                        "default": 1,
                        "minimum": 1
                    },
                    "since": {
                        "type": "string",
                        "title": "Since",
                        "description": "Дата начала в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"
                    },
                    "until": {
                        "type": "string",
                        "title": "Until",
                        "description": "Дата окончания в формате ISO 8601 (например, 2024-12-31T23:59:59Z)"
                    },
                    "author": {
                        "type": "string",
                        "title": "Author",
                        "description": "Имя пользователя автора коммитов"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="aiohttp",
            examples=[
                {
                    "title": "Получение последних коммитов",
                    "config": {
                        "repository": "owner/repo",
                        "branch": "main",
                        "per_page": 10
                    }
                },
                {
                    "title": "Получение коммитов за период",
                    "config": {
                        "repository": "owner/repo",
                        "since": "2024-01-01T00:00:00Z",
                        "until": "2024-12-31T23:59:59Z",
                        "per_page": 50
                    }
                },
                {
                    "title": "Получение коммитов конкретного автора",
                    "config": {
                        "repository": "owner/repo",
                        "author": "github-username",
                        "per_page": 20
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
        Выполняет интеграцию для получения списка коммитов из GitHub.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        # Получаем GitHub токен из credentials
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

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        github_token = payload.get("token")
        if not github_token:
            await logger.error("GitHub token not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }

        # Получаем параметры из config
        repository = config.get("repository")
        if not repository:
            await logger.error("repository is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "repository is required"
                }
            }

        branch = config.get("branch", "main")
        per_page = config.get("per_page", 30)
        page = config.get("page", 1)
        since = config.get("since")
        until = config.get("until")
        author = config.get("author")

        # Строим URL для получения коммитов
        url = f"https://api.github.com/repos/{repository}/commits"
        
        # Параметры запроса
        params = {
            "sha": branch,
            "per_page": per_page,
            "page": page
        }
        
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        if author:
            params["author"] = author

        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json"
        }

        try:
            async with ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        error_message = await response.text()
                        await logger.error(f"Failed to get commits. HTTP status: {response.status}, Response: {error_message}")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": response.status,
                                "description": f"Failed to get commits. Response: {error_message}"
                            }
                        }

                    commits = await response.json()

            # Форматируем результат
            formatted_commits: List[Dict[str, Any]] = []
            for commit in commits:
                formatted_commit = {
                    "sha": commit.get("sha"),
                    "message": commit.get("commit", {}).get("message"),
                    "author": {
                        "name": commit.get("commit", {}).get("author", {}).get("name"),
                        "email": commit.get("commit", {}).get("author", {}).get("email"),
                        "username": commit.get("author", {}).get("login") if commit.get("author") else None
                    },
                    "committer": {
                        "name": commit.get("commit", {}).get("committer", {}).get("name"),
                        "email": commit.get("commit", {}).get("committer", {}).get("email"),
                        "username": commit.get("committer", {}).get("login") if commit.get("committer") else None
                    },
                    "date": commit.get("commit", {}).get("author", {}).get("date"),
                    "url": commit.get("html_url")
                }
                formatted_commits.append(formatted_commit)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "commits": formatted_commits,
                        "count": len(formatted_commits),
                        "repository": repository,
                        "branch": branch,
                        "page": page,
                        "per_page": per_page
                    }
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
