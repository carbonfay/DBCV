"""GitHub Create Pull Request интеграция используя библиотеку aiohttp."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
from aiohttp import ClientSession

class GitHubCreatePullRequestIntegration(BaseIntegration):
    """Интеграция для создания Pull Request в GitHub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_pull_request",
            version="1.0.0",
            name="GitHub Create Pull Request",
            description="Создание Pull Request в GitHub через API",
            category="version_control",
            icon_s3_key="icons/integrations/github.svg",
            color="#181717",
            config_schema={
                "type": "object",
                "required": ["repository", "title", "head", "base"],
                "properties": {
                    "repository": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Полное имя репозитория (например, owner/repo)"
                    },
                    "title": {
                        "type": "string",
                        "title": "Title",
                        "description": "Заголовок Pull Request"
                    },
                    "head": {
                        "type": "string",
                        "title": "Head Branch",
                        "description": "Имя ветки, из которой создается Pull Request"
                    },
                    "base": {
                        "type": "string",
                        "title": "Base Branch",
                        "description": "Имя ветки, в которую создается Pull Request"
                    },
                    "body": {
                        "type": "string",
                        "title": "Body",
                        "description": "Описание Pull Request"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="aiohttp",
            examples=[
                {
                    "title": "Создание Pull Request",
                    "config": {
                        "repository": "owner/repo",
                        "title": "Add new feature",
                        "head": "feature-branch",
                        "base": "main",
                        "body": "This PR adds a new feature."
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
        Выполняет интеграцию для создания Pull Request в GitHub.

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
        title = config.get("title")
        head = config.get("head")
        base = config.get("base")
        body = config.get("body")

        if not repository or not title or not head or not base:
            await logger.error("repository, title, head, and base are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "repository, title, head, and base are required"
                }
            }

        # Создаем Pull Request через GitHub API
        url = f"https://api.github.com/repos/{repository}/pulls"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json"
        }
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }

        try:
            async with ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status != 201:
                        error_message = await response.text()
                        await logger.error(f"Failed to create Pull Request. HTTP status: {response.status}, Response: {error_message}")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": response.status,
                                "description": f"Failed to create Pull Request. Response: {error_message}"
                            }
                        }

                    result = await response.json()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "url": result.get("html_url"),
                        "id": result.get("id"),
                        "number": result.get("number"),
                        "state": result.get("state")
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