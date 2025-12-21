"""AmoCRM Create Task integration using httpx for direct REST requests."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx напрямую
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False


class AmoCrmCreateTaskIntegration(BaseIntegration):
    """Интеграция для создания задачи в AmoCRM через REST API (httpx)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_create_task",
            version="1.0.0",
            name="AmoCRM Create Task",
            description="Создать задачу (task) в AmoCRM для сущности (lead/contact/company).",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#F05A28",
            config_schema={
                "type": "object",
                "required": ["entity_id", "entity_type", "text"],
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "title": "Entity Type",
                        "description": "Тип сущности, к которой привязывается задача (leads, contacts, companies)",
                        "enum": ["leads", "contacts", "companies"],
                        "default": "leads"
                    },
                    "entity_id": {
                        "type": "string",
                        "title": "Entity ID",
                        "description": "ID сущности в AmoCRM (можно использовать переменные: {$lead.id$})"
                    },
                    "text": {
                        "type": "string",
                        "title": "Task Text",
                        "description": "Текст задачи"
                    },
                    "complete_till": {
                        "type": "integer",
                        "title": "Complete Till (unix)",
                        "description": "Время дедлайна в секундах с начала эпохи (опционально)"
                    },
                    "task_type_id": {
                        "type": "integer",
                        "title": "Task Type ID",
                        "description": "ID типа задачи в AmoCRM (опционально)"
                    },
                    "responsible_user_id": {
                        "type": "integer",
                        "title": "Responsible User ID",
                        "description": "ID ответственного пользователя в AmoCRM (опционально)"
                    }
                }
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Create task for lead",
                    "config": {
                        "entity_type": "leads",
                        "entity_id": "{$lead.id$}",
                        "text": "Call the client tomorrow",
                        "complete_till": 1700000000
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Создаёт задачу в AmoCRM используя httpx.

        Ожидаемые параметры в config:
          - entity_type: "leads" | "contacts" | "companies" (обязательно)
          - entity_id: ID сущности в AmoCRM (обязательно)
          - text: текст задачи (обязательно)
          - complete_till: unix timestamp (опционально)
          - task_type_id: integer (опционально)
          - responsible_user_id: integer (опционально)

        Возвращает: {"response": {"ok": True, "result": {...}}} или ошибка
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

        entity_type = config.get("entity_type", "leads")
        entity_id = config.get("entity_id")
        text = config.get("text")
        complete_till = config.get("complete_till")
        task_type_id = config.get("task_type_id")
        responsible_user_id = config.get("responsible_user_id")

        if not entity_id or not text:
            await logger.error("entity_id and text are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "entity_id and text are required"
                }
            }

        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="amocrm",
            strategy="oauth",
        )

        if not creds:
            await logger.error("AmoCRM credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "AmoCRM credentials not found"
                }
            }

        payload = creds.get("payload", {}) or creds
        base_domain = payload.get("base_domain")
        if not base_domain:
            await logger.error("base_domain not found in AmoCRM credentials payload")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "base_domain not found in credentials payload"
                }
            }

        # Подготовим заголовки через AuthService, чтобы получить/обновить токен
        try:
            from app.auth.service import AuthService

            auth = AuthService(credentials_resolver)
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            await auth.apply(
                bot_id=str(bot_id),
                headers=headers,
                request_url=f"https://{base_domain}/api/v4/tasks",
            )
        except Exception as e:
            await logger.error(f"Error obtaining auth headers for AmoCRM: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Error obtaining auth headers: {e}"
                }
            }

        # Сбор данных для запроса (AmoCRM ожидает массив задач)
        try:
            task_obj: Dict[str, Any] = {
                "text": str(text),
                "entity_id": int(entity_id) if str(entity_id).isdigit() else entity_id,
                "entity_type": entity_type,
            }
            if complete_till is not None:
                task_obj["complete_till"] = int(complete_till)
            if task_type_id is not None:
                task_obj["task_type_id"] = int(task_type_id)
            if responsible_user_id is not None:
                task_obj["responsible_user_id"] = int(responsible_user_id)

            url = f"https://{base_domain}/api/v4/tasks"
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(url, json=[task_obj], headers=headers)
                # Если ошибка HTTP — пробрасываем
                try:
                    r.raise_for_status()
                except httpx.HTTPStatusError as e:
                    await logger.error(f"AmoCRM API status error: {e} - body: {r.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": r.status_code,
                            "description": r.text
                        }
                    }

                j = r.json() if r.content else {}

            # Возвращаем полезную часть ответа
            return {
                "response": {
                    "ok": True,
                    "result": j
                }
            }

        except Exception as e:
            await logger.error(f"Unexpected error creating AmoCRM task: {e}")
            import traceback

            traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"Traceback: {traceback_str}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
