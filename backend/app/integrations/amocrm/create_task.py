"""AmoCRM Create Task интеграция используя httpx.

Использует OAuth credentials (provider: "amocrm", strategy: "oauth").
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импорт библиотеки httpx
try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False


class AmoCRMIntegration(BaseIntegration):
    """Интеграция для создания задачи в AmoCRM через API v4 (httpx)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_create_task",
            version="1.0.0",
            name="AmoCRM Create Task",
            description="Создать задачу (task) в AmoCRM через API v4",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#E85326",
            config_schema={
                "type": "object",
                "required": ["subdomain", "text"],
                "properties": {
                    "subdomain": {
                        "type": "string",
                        "title": "Subdomain",
                        "description": "Поддомен AmoCRM (например, mycompany.amocrm.ru)"
                    },
                    "text": {
                        "type": "string",
                        "title": "Task text",
                        "description": "Текст задачи"
                    },
                    "task_type_id": {
                        "type": "integer",
                        "title": "Task Type ID",
                        "description": "Тип задачи в AmoCRM (например, 1 - звонок, 2 - задача)"
                    },
                    "complete_till": {
                        "type": "integer",
                        "title": "Complete Till",
                        "description": "Время завершения в формате Unix timestamp (секунды)"
                    },
                    "entity_id": {
                        "type": "integer",
                        "title": "Entity ID",
                        "description": "ID сущности (lead/contact/company) для привязки задачи"
                    },
                    "entity_type": {
                        "type": "string",
                        "title": "Entity Type",
                        "enum": ["leads", "contacts", "companies"],
                        "description": "Тип сущности для привязки задачи"
                    },
                    "responsible_user_id": {
                        "type": "integer",
                        "title": "Responsible User ID",
                        "description": "ID ответственного пользователя в AmoCRM"
                    }
                }
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Create simple task",
                    "config": {
                        "subdomain": "mycompany.amocrm.ru",
                        "text": "Call the client",
                        "task_type_id": 1
                    }
                },
                {
                    "title": "Create task linked to a lead",
                    "config": {
                        "subdomain": "mycompany.amocrm.ru",
                        "text": "Follow up on lead",
                        "entity_id": 12345678,
                        "entity_type": "leads",
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
        """Создаёт задачу в AmoCRM.

        Порядок действий:
        - Проверяет доступность библиотеки httpx
        - Получает credentials через credentials_resolver.get_default_for()
        - Обновляет access_token через endpoint /oauth2/access_token (refresh_token grant)
        - Выполняет POST /api/v4/tasks
        - Обрабатывает ошибки
        - Возвращает результат в формате {"response": {"ok": True, "result": {...}}}
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

        # Список ожидаемых полей
        subdomain = config.get("subdomain")
        text = config.get("text")
        task_type_id = config.get("task_type_id")
        complete_till = config.get("complete_till")
        entity_id = config.get("entity_id")
        entity_type = config.get("entity_type")
        responsible_user_id = config.get("responsible_user_id")

        if not subdomain or not text:
            await logger.error("subdomain and text are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "subdomain and text are required"
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
        base_domain = payload.get("base_domain") or subdomain
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        redirect_uri = payload.get("redirect_uri")
        refresh_token = payload.get("refresh_token")

        if not base_domain:
            await logger.error("base_domain is required in credentials or config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "base_domain is required in credentials or config"
                }
            }

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                # Получаем access_token используя refresh_token (если есть refresh_token в credentials)
                access_token: Optional[str] = None
                token_type: str = "Bearer"

                if refresh_token and client_id and client_secret and redirect_uri:
                    token_url = f"https://{base_domain}/oauth2/access_token"
                    token_payload = {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "redirect_uri": redirect_uri,
                    }
                    try:
                        r = await client.post(token_url, json=token_payload)
                        r.raise_for_status()
                        j = r.json()
                        access_token = j.get("access_token")
                        token_type = j.get("token_type", "Bearer")
                    except httpx.HTTPStatusError as e:
                        await logger.error(f"Failed to refresh token: {e} (status {e.response.status_code})")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": e.response.status_code,
                                "description": f"Token refresh failed: {e.response.text}"
                            }
                        }
                else:
                    # Попробуем взять access_token прямо из payload (если был сохранён)
                    access_token = payload.get("access_token")

                if not access_token:
                    await logger.error("access_token is not available (refresh_token flow failed or missing)")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 401,
                            "description": "Could not obtain access_token for AmoCRM"
                        }
                    }

                # Формируем тело задачи
                task_data: Dict[str, Any] = {"text": str(text)}
                if task_type_id is not None:
                    task_data["task_type_id"] = int(task_type_id)
                if complete_till is not None:
                    task_data["complete_till"] = int(complete_till)
                if responsible_user_id is not None:
                    task_data["responsible_user_id"] = int(responsible_user_id)

                if entity_id is not None and entity_type is not None:
                    task_data["entity_id"] = int(entity_id)
                    task_data["entity_type"] = str(entity_type)

                url = f"https://{base_domain}/api/v4/tasks"
                headers = {"Authorization": f"{token_type} {access_token}"}

                resp = await client.post(url, headers=headers, json=[task_data])
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    await logger.error(f"AmoCRM API error: {e} (status {e.response.status_code})")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": e.response.status_code,
                            "description": e.response.text
                        }
                    }

                # Успех — возвращаем тело ответа
                j = resp.json()
                # AmoCRM возвращает массив созданных задач (в теле ответа или в _embedded) — возвращаем весь JSON
                return {
                    "response": {
                        "ok": True,
                        "result": j
                    }
                }

        except Exception as e:
            await logger.error(f"Unexpected error when creating AmoCRM task: {e}")
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
