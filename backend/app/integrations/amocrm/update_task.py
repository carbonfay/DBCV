"""AmoCRM Update Task интеграция используя прямые HTTP запросы через httpx.

Поддерживает обновление полей задачи в AmoCRM v4 API по ID задачи.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx напрямую
try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:  # ImportError или любые проблемы
    httpx = None
    HTTPX_AVAILABLE = False


class AmocrmUpdateTaskIntegration(BaseIntegration):
    """Интеграция для обновления задачи в AmoCRM через REST API (httpx)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_update_task",
            version="1.0.0",
            name="AmoCRM Update Task",
            description="Обновление полей задачи в AmoCRM через REST API (v4)",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#ff5722",
            config_schema={
                "type": "object",
                "required": ["task_id"],
                "properties": {
                    "task_id": {
                        "type": "string",
                        "title": "Task ID",
                        "description": "ID задачи AmoCRM"
                    },
                    "text": {
                        "type": "string",
                        "title": "Text",
                        "description": "Текст задачи"
                    },
                    "complete_till": {
                        "type": "integer",
                        "title": "Complete Till",
                        "description": "Unix timestamp завершения (в секундах)"
                    },
                    "is_completed": {
                        "type": "boolean",
                        "title": "Is Completed",
                        "description": "Пометить задачу как выполненную"
                    },
                    "responsible_user_id": {
                        "type": "integer",
                        "title": "Responsible User ID",
                        "description": "ID ответственного пользователя"
                    },
                    "custom_fields": {
                        "type": "object",
                        "additionalProperties": True,
                        "title": "Custom Fields",
                        "description": "Объект с дополнительными полями задачи (ключи и значения передаются как есть)"
                    }
                }
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Обновить текст задачи",
                    "config": {
                        "task_id": "12345678",
                        "text": "New task text from DBCV"
                    }
                },
                {
                    "title": "Отметить задачу выполненной",
                    "config": {
                        "task_id": "12345678",
                        "is_completed": True
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
        """Выполняет обновление задачи в AmoCRM.

        Ожидаемые credentials (payload):
        - access_token: OAuth access token
        - domain / site / base_url: домен AmoCRM (например, subdomain.amocrm.ru или https://subdomain.amocrm.ru)
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

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="amocrm",
            strategy="oauth"
        )

        if not creds:
            await logger.error("AmoCRM credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "AmoCRM credentials not found"}}

        payload = creds.get("payload") or creds

        access_token = payload.get("access_token") or payload.get("token")
        if not access_token:
            await logger.error("access_token not found in AmoCRM credentials")
            return {"response": {"ok": False, "error_code": 401, "description": "access_token not found in credentials"}}

        # Определяем базовый URL для AmoCRM
        base_url: Optional[str] = None
        for k in ("domain", "site", "base_url", "account"):
            val = payload.get(k)
            if val:
                base_url = str(val)
                break

        if not base_url:
            # Иногда domain хранится как subdomain (только поддомен)
            subdomain = payload.get("subdomain")
            if subdomain:
                base_url = f"https://{subdomain}"

        if not base_url:
            await logger.error("AmoCRM base URL not found in credentials (domain/site/base_url)")
            return {"response": {"ok": False, "error_code": 401, "description": "AmoCRM domain (site/base_url) not found in credentials"}}

        # Убедимся, что base_url имеет схему
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        task_id = config.get("task_id")
        if not task_id:
            await logger.error("task_id is required in config")
            return {"response": {"ok": False, "error_code": 400, "description": "task_id is required"}}

        # Сформируем тело запроса из переданных параметров
        body: Dict[str, Any] = {}
        for key in ("text", "complete_till", "is_completed", "responsible_user_id", "custom_fields"):
            if key in config:
                body[key] = config.get(key)

        if not body:
            await logger.warning("No updatable fields provided in config")

        url = f"{base_url.rstrip('/')}/api/v4/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.patch(url, json=body, headers=headers)

                # Если статус успешный (2xx)
                if 200 <= response.status_code < 300:
                    try:
                        data = response.json() if response.content else {}
                    except Exception:
                        data = {"status_code": response.status_code, "content": response.text}

                    return {"response": {"ok": True, "result": data}}

                # Ошибки API
                await logger.error(f"AmoCRM API error: {response.status_code} - {response.text}")
                return {"response": {"ok": False, "error_code": response.status_code, "description": response.text}}

        except httpx.RequestError as e:
            await logger.error(f"AmoCRM request error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error updating AmoCRM task: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
