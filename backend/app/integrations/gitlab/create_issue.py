"""GitLab Create Issue интеграция."""
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

class GitLabCreateIssueIntegration(BaseIntegration):
    """Интеграция для создания Issue в GitLab (аналог curl запроса)."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="create_issue",
            version="1.0.0",
            name="GitLab Create Issue",
            description="Создание новой задачи (Issue) в репозитории GitLab",
            category="development",
            icon_s3_key="icons/integrations/gitlab.svg",
            color="#9966cc", 
            # documentation_url="https://docs.gitlab.com/ee/api/issues.html", 
            # Схема на основе параметров из curl: URL path params + JSON body
            config_schema={
                "type": "object",
                "required": ["projects", "project_id", "title", "labels"],
                "properties": {
                    "projects": {
                        "type": "string",
                        "title": "projects",
                        "description": "projects"
                    },
                    "project_id": {
                        "type": "string",
                        "title": "project_id",
                        "description": "ID репозитория (например, '123456')"
                    },
                    "title": {
                        "type": "string",
                        "title": "text",
                        "description": "Text"
                    },
                    "labels": {
                        "type": "string",
                        "title": "Labels",
                        "description": "Labels"

                    }
                }
            },
             # Указываем, что нам нужен токен от провайдера gitlab
            credentials_provider="other",
            credentials_strategy="api_key", # 
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Создание баг-репорта",
                    "config": { 
                        "projects": "PROJECTS",
                        "project_id": "PROJECT_ID",                     
                        "title": "Issues with auth from DBCV",
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
        """Выполняет HTTP запрос к GitLab"""  
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
        # 1. Получаем токен из Credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        if not creds:
            await logger.error("GitLab credentials not found or invalid")
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
                    "description": "token not found in credentials"
                }
            }   
        # 2. Подготовка данных из config (парсим строки в списки для JSON)
        projects = config.get("projects")
        project_id = config.get("project_id")
                  
            # Формируем JSON Body (-d '{...}')
        json_body = {"title": config.get("title"), "labels": config.get("labels")} 
            # 3. Подготовка запроса (Headers и URL)
        url = f"https://gitlab.com/api/v4/{projects}/{project_id}/issues"
        
        headers = {
            "PRIVATE-TOKEN": token
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
                    await logger.info(f"GitLab issue created: {response_data.get('html_url')}")
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