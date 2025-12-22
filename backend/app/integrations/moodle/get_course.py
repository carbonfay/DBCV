"""Moodle Get Course интеграция используя httpx для прямых запросов к Moodle Web Services API."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx для прямых HTTP запросов к Moodle API
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class MoodleGetCourseIntegration(BaseIntegration):
    """Интеграция для получения информации о курсе Moodle через Web Services API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_course",
            version="1.0.0",
            name="Moodle Get Course",
            description="Получение информации о курсе Moodle по полю (id, shortname, idnumber)",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#F98012",
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
                        "description": "Значение поля для поиска (можно использовать переменные: {$course.id$})"
                    }
                }
            },
            credentials_provider="moodle",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить курс по ID",
                    "config": {
                        "field": "id",
                        "value": "{$course.id$}"
                    }
                },
                {
                    "title": "Получить курс по shortname",
                    "config": {
                        "field": "shortname",
                        "value": "MATH101"
                    }
                },
                {
                    "title": "Получить курс по idnumber",
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
                - field: Поле для поиска (id, shortname, idnumber)
                - value: Значение поля
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
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
            provider="moodle",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Moodle credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle credentials not found"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        moodle_url = payload.get("moodle_url") or payload.get("url")
        token = payload.get("token") or payload.get("api_key") or payload.get("wstoken")
        
        if not moodle_url:
            await logger.error(f"moodle_url not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "moodle_url not found in credentials"
                }
            }
        
        if not token:
            await logger.error(f"token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "token not found in credentials"
                }
            }
        
        # Получаем параметры из config
        field = config.get("field", "id")
        value = config.get("value")
        
        if not value:
            await logger.error("value is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "value is required"
                }
            }
        
        # Валидация field
        if field not in ["id", "shortname", "idnumber"]:
            await logger.error(f"Invalid field: {field}. Must be one of: id, shortname, idnumber")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid field: {field}. Must be one of: id, shortname, idnumber"
                }
            }
        
        # Нормализуем URL (убираем trailing slash)
        moodle_url = moodle_url.rstrip("/")
        
        # Формируем URL для Moodle Web Services API
        api_url = f"{moodle_url}/webservice/rest/server.php"
        
        # Параметры запроса
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
                
                # Moodle API может вернуть исключение в формате JSON
                if isinstance(result, dict) and "exception" in result:
                    error_message = result.get("message", "Unknown Moodle API error")
                    error_code = result.get("errorcode", "unknown")
                    await logger.error(f"Moodle API error: {error_code} - {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"Moodle API error: {error_code} - {error_message}"
                        }
                    }
                
                # Проверяем, что результат - это список курсов
                if isinstance(result, list) and len(result) > 0:
                    # Возвращаем первый курс (по полю и значению должен быть только один)
                    course = result[0]
                    await logger.info(f"Successfully retrieved course: {course.get('id')} - {course.get('fullname')}")
                    return {
                        "response": {
                            "ok": True,
                            "result": course
                        }
                    }
                elif isinstance(result, list) and len(result) == 0:
                    await logger.warning(f"Course not found with {field}={value}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Course not found with {field}={value}"
                        }
                    }
                else:
                    # Неожиданный формат ответа
                    await logger.error(f"Unexpected response format: {type(result)}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": f"Unexpected response format from Moodle API: {type(result)}"
                        }
                    }
                    
        except httpx.HTTPStatusError as e:
            await logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"HTTP error: {e.response.status_code} - {e.response.text[:200]}"
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
            import traceback
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"Traceback: {traceback_str}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }









