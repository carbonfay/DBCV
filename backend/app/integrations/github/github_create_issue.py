"""GitHub Create Issue интеграция."""
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Проверяем наличие библиотеки httpx для выполнения HTTP запросов
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class GitHubCreateIssueIntegration(BaseIntegration):
    """Интеграция для создания Issue в GitHub (аналог curl запроса)."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_issue",
            version="1.0.0",
            name="GitHub Create Issue",
            description="Создание новой задачи (Issue) в репозитории GitHub",
            category="development",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292f",
            # Схема на основе параметров из curl: URL path params + JSON body
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Owner",
                        "description": "Владелец репозитория (например, 'facebook')"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository",
                        "description": "Название репозитория (например, 'react')"
                    },
                    "title": {
                        "type": "string",
                        "title": "Issue Title",
                        "description": "Заголовок задачи"
                    },
                    "body": {
                        "type": "string",
                        "title": "Issue Body",
                        "description": "Описание задачи",
                        "widget": "textarea" # Подсказка для UI использовать многострочное поле
                    },
                    "assignees": {
                        "type": "string",
                        "title": "Assignees",
                        "description": "Логины исполнителей через запятую (например: akmsher, user2)"
                    },
                    "labels": {
                        "type": "string",
                        "title": "Labels",
                        "description": "Метки через запятую (например: bug, funny bug)"
                    }
                }
            },
            # Указываем, что нам нужен токен от провайдера github
            credentials_provider="other",
            credentials_strategy="api_key", # Обычно GitHub использует Bearer Token
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Создание баг-репорта",
                    "config": {
                        "owner": "OWNER",
                        "repo": "REPO",
                        "title": "Chao from DBCV!!!",
                        "body": "I'm having a problem with this.",
                        "assignees": "akmsher",
                        "labels": "bug"
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
        Выполняет HTTP запрос к GitHub API.
        """
        if not HTTPX_AVAILABLE:
            error_msg = "httpx library is not installed"
            await logger.error(error_msg)
            return {
                "response": {
                    "ok": False, 
                    "error_code": 500, 
                    "description": error_msg
                }
            }
        
        # 1. Получаем токен из Credentials (Authorization: Bearer token)
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("GitHub credentials not found or invalid")
            return {"response": {"ok": False, "error": "Credentials missing"}}

        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        token = payload.get("token") or payload.get("bot-token")
        if not token:
            await logger.error(f"token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }

        # 2. Подготовка данных из config (парсим строки в списки для JSON)
        owner = config.get("owner")
        repo = config.get("repo")
        
        # Обработка списков (в форме они вводятся как строки через запятую)
        assignees_str = config.get("assignees", "")
        assignees_list = [x.strip() for x in assignees_str.split(",")] if assignees_str else []
        
        labels_str = config.get("labels", "")
        labels_list = [x.strip() for x in labels_str.split(",")] if labels_str else []

        # Формируем JSON Body (-d '{...}')
        json_body = {
            "title": config.get("title"),
            "body": config.get("body", ""),
            "assignees": assignees_list,
            "labels": labels_list
        }

        # 3. Подготовка запроса (Headers и URL)
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # 4. Выполнение запроса
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    headers=headers, 
                    json=json_body,
                    timeout=10.0
                )
                
                response_data = response.json()
                
                # Логируем результат для отладки
                if response.is_success:
                    await logger.info(f"GitHub issue created: {response_data.get('html_url')}")
                    return {
                        "response": {
                            "ok": True,
                            "status_code": response.status_code,
                            "data": response_data
                        }
                    }
                else:
                    await logger.warning(f"GitHub API Error: {response.text}")
                    return {
                        "response": {
                            "ok": False,
                            "status_code": response.status_code,
                            "description": response_data.get("message", "Unknown error")
                        }
                    }

            except Exception as e:
                await logger.error(f"Request failed: {str(e)}")
                return {
                    "response": {
                        "ok": False,
                        "description": str(e)
                    }
                }

