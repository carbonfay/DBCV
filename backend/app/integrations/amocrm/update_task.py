"""AmoCRM Update Task интеграция используя httpx.

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


class AmoCRMUpdateTaskIntegration(BaseIntegration):
    """Интеграция для обновления задачи в AmoCRM через API v4 (httpx)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_update_task",
            version="1.0.0",
            name="AmoCRM Update Task",
            description="Обновить задачу (task) в AmoCRM через API v4",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#E85326",
            config_schema={
                "type": "object",
                "required": ["subdomain", "task_id"],
                "properties": {
                    "subdomain": {
                        "type": "string",
                        "title": "Subdomain",
                        "description": "Поддомен AmoCRM (например, mycompany.amocrm.ru)"
                    },
                    "task_id": {
                        "type": "integer",
                        "title": "Task ID",
                        "description": "ID задачи в AmoCRM"
                    },
                    "text": {
                        "type": "string",
                        "title": "Task text",
                        "description": "Обновлённый текст задачи"
                    },
                    "task_type_id": {
                        "type": "integer",
                        "title": "Task Type ID",
                        "description": "Тип задачи в AmoCRM"
                    },
                    "complete_till": {
                        "type": "integer",
                        "title": "Complete Till",
                        "description": "Время завершения в формате Unix timestamp (секунды)"
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
                    "title": "Update task text",
                    "config": {
                        "subdomain": "mycompany.amocrm.ru",
                        "task_id": 12345,
                        "text": "Updated text"
                    }
                },
                {
                    "title": "Update task responsible and deadline",
                    "config": {
                        "subdomain": "mycompany.amocrm.ru",
                        "task_id": 12345,
                        "responsible_user_id": 54321,
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
        """Обновляет задачу в AmoCRM.

        Шаги:
        - Проверяет наличие httpx
        - Получает credentials через credentials_resolver.get_default_for()
        - Обновляет access_token через refresh_token (если есть) или использует сохранённый access_token
        - Выполняет PATCH /api/v4/tasks/{task_id}
        - Обрабатывает ошибки и возвращает результат в формате {"response": {"ok": True/False, ...}}
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

        subdomain = config.get("subdomain")
        task_id = config.get("task_id")
        text = config.get("text")
        task_type_id = config.get("task_type_id")
        complete_till = config.get("complete_till")
        responsible_user_id = config.get("responsible_user_id")

        if not subdomain or not task_id:
            await logger.error("subdomain and task_id are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "subdomain and task_id are required"
                }
            }

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

                task_data: Dict[str, Any] = {}
                if text is not None:
                    task_data["text"] = str(text)
                if task_type_id is not None:
                    task_data["task_type_id"] = int(task_type_id)
                if complete_till is not None:
                    task_data["complete_till"] = int(complete_till)
                if responsible_user_id is not None:
                    task_data["responsible_user_id"] = int(responsible_user_id)

                if not task_data:
                    await logger.error("No updatable fields provided for task")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "No updatable fields provided"
                        }
                    }

                url = f"https://{base_domain}/api/v4/tasks/{int(task_id)}"
                headers = {"Authorization": f"{token_type} {access_token}"}

                resp = await client.patch(url, headers=headers, json=task_data)
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    await logger.error(f"AmoCRM API error when updating task: {e} (status {e.response.status_code})")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": e.response.status_code,
                            "description": e.response.text
                        }
                    }

                j = resp.json()
                return {
                    "response": {
                        "ok": True,
                        "result": j
                    }
                }

        except Exception as e:
            await logger.error(f"Unexpected error when updating AmoCRM task: {e}")
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
