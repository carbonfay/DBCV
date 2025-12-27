"""Moodle Get Course интеграция используя httpx для прямых запросов к Moodle Web Services API."""
from typing import Dict, Any
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MoodleGetCourseIntegration(BaseIntegration):
    """Интеграция для получения информации о курсе из Moodle через Web Services API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_course",
            version="1.0.0",
            name="Moodle Get Course",
            description="Получение информации о курсе из Moodle по ID, короткому имени или номеру",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#f98012",
            config_schema={
                "type": "object",
                "required": ["field", "value"],
                "properties": {
                    "field": {
                        "type": "string",
                        "title": "Field",
                        "description": "Поле для поиска курса",
                        "enum": ["id", "shortname", "idnumber"],
                        "default": "id"
                    },
                    "value": {
                        "type": "string",
                        "title": "Value",
                        "description": "Значение поля (ID курса, короткое имя или номер)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Получить курс по ID",
                    "config": {
                        "field": "id",
                        "value": "5"
                    }
                },
                {
                    "title": "Получить курс по короткому имени",
                    "config": {
                        "field": "shortname",
                        "value": "MATH101"
                    }
                },
                {
                    "title": "Получить курс по номеру",
                    "config": {
                        "field": "idnumber",
                        "value": "COURSE-2024-001"
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
        Выполняет интеграцию используя httpx для прямых запросов к Moodle Web Services API.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Moodle credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle credentials not found. Please configure credentials with provider='other' and strategy='api_key'"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        # Получаем URL сервера Moodle и токен
        moodle_url = payload.get("url") or payload.get("moodle_url") or payload.get("server_url")
        token = payload.get("token") or payload.get("wstoken") or payload.get("api_key")
        
        if not moodle_url:
            await logger.error("Moodle URL not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle URL not found in credentials. Available keys: " + str(list(payload.keys()))
                }
            }
        
        if not token:
            await logger.error("Moodle token not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle token (wstoken) not found in credentials. Available keys: " + str(list(payload.keys()))
                }
            }
        
        # Получаем параметры из config
        field = config.get("field", "id")
        value = config.get("value")
        
        if not value:
            await logger.error("field and value are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "field and value are required"
                }
            }
        
        # Проверяем, что field валидный
        if field not in ["id", "shortname", "idnumber"]:
            await logger.error(f"Invalid field: {field}. Must be one of: id, shortname, idnumber")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid field: {field}. Must be one of: id, shortname, idnumber"
                }
            }
        
        # Формируем URL для Moodle Web Services API
        # Убираем trailing slash если есть
        moodle_url = moodle_url.rstrip("/")
        api_url = f"{moodle_url}/webservice/rest/server.php"
        
        # Параметры для Moodle REST API
        params = {
            "wstoken": token,
            "wsfunction": "core_course_get_courses_by_field",
            "moodlewsrestformat": "json",
            "field": field,
            "value": str(value)
        }
        
        # ИСПОЛЬЗУЕМ httpx ДЛЯ ПРЯМЫХ ЗАПРОСОВ К MOODLE API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                result = response.json()
                
                # Moodle может вернуть ошибку в формате JSON
                if isinstance(result, dict) and "exception" in result:
                    error_message = result.get("message", "Unknown Moodle error")
                    error_code = result.get("errorcode", "moodle_error")
                    await logger.error(f"Moodle API error: {error_code} - {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"Moodle API error: {error_code} - {error_message}"
                        }
                    }
                
                # Возвращаем результат в формате системы
                return {
                    "response": {
                        "ok": True,
                        "result": result
                    }
                }
        except httpx.HTTPStatusError as e:
            await logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"HTTP error: {e.response.status_code} - {str(e)}"
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"Request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Request error: {str(e)}"
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

