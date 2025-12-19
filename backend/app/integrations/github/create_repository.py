from typing import Dict, Any
from uuid import UUID

import json
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class GitHubCreateRepositoryIntegration(BaseIntegration):

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github.create_repository",
            version="1.0.0",
            name="GitHub: Create Repository",
            description="Создает новый репозиторий в GitHub от имени аутентифицированного пользователя.",
            category="devtools",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {
                        "type": "string",
                        "title": "Repository name",
                        "description": "Имя репозитория (например, my-new-repo).",
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание репозитория.",
                    },
                    "private": {
                        "type": "boolean",
                        "title": "Private repository",
                        "description": "Создавать ли приватный репозиторий.",
                        "default": True,
                    },
                    "auto_init": {
                        "type": "boolean",
                        "title": "Auto init",
                        "description": "Инициализировать ли репозиторий с README.md.",
                        "default": True,
                    },
                    "default_branch": {
                        "type": "string",
                        "title": "Default branch",
                        "description": "Имя ветки по умолчанию (например, main). Оставь пустым для значения по умолчанию GitHub.",
                    },
                },
            },
            # ВАЖНО: используем существующий провайдер other + api_key
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.24.0",
            examples=[
                {
                    "title": "Создание приватного репозитория",
                    "config": {
                        "name": "my-awesome-repo",
                        "description": "Практика DBCV",
                        "private": True,
                        "auto_init": True,
                    },
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key",
        )

        if not creds:
            await logger.error("GitHub credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub credentials not found",
                }
            }

        payload = creds.get("payload") or creds
        token = payload.get("token") or payload.get("access_token")

        if not token:
            await logger.error(
                f"GitHub token not found in credentials. Available keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials",
                }
            }

        repo_name = config.get("name")
        description = config.get("description")
        private = bool(config.get("private", True))
        auto_init = bool(config.get("auto_init", True))
        default_branch = config.get("default_branch")

        if not repo_name:
            await logger.error("Repository name is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Repository name (name) is required",
                }
            }

        api_url = "https://api.github.com/user/repos"

        body: Dict[str, Any] = {
            "name": repo_name,
            "private": private,
            "auto_init": auto_init,
        }
        if description:
            body["description"] = description
        if default_branch:
            body["default_branch"] = default_branch

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(api_url, json=body, headers=headers)

            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "full_name": data.get("full_name"),
                            "private": data.get("private"),
                            "html_url": data.get("html_url"),
                            "description": data.get("description"),
                            "default_branch": data.get("default_branch"),
                        },
                    }
                }
            
            try:
                error_data = response.json()
            except json.JSONDecodeError:
                error_data = {"message": response.text}

            await logger.error(
                f"GitHub API error: {response.status_code} {error_data}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": response.status_code,
                    "description": error_data.get("message")
                    or "GitHub API error",
                    "details": error_data,
                }
            }

        except httpx.RequestError as exc:
            await logger.error(f"GitHub request error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"GitHub request error: {exc}",
                }
            }
        except Exception as exc:
            await logger.error(f"Unexpected GitHub integration error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(exc),
                }
            }
