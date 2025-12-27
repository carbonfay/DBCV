"""Moodle Get Course интеграция используя httpx для прямых запросов к Moodle Web Services API."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
import httpx


class MoodleGetCourseIntegration(BaseIntegration):
    """Интеграция для получения информации о курсе Moodle через Web Services API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_course",
            version="1.0.0",
            name="Moodle Get Course",
            description="Получение информации о курсе Moodle по ID через Web Services API",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#f98012",
            config_schema={
                "type": "object",
                "required": ["course_id"],
                "properties": {
                    "course_id": {
                        "type": ["integer", "string"],
                        "title": "Course ID",
                        "description": "ID курса в Moodle (можно использовать переменные: {$course.id$})"
                    },
                    "field": {
                        "type": "string",
                        "title": "Field",
                        "description": "Поле для поиска курса (по умолчанию: 'id')",
                        "enum": ["id", "shortname", "idnumber", "category"],
                        "default": "id"
                    }
                }
            },
            credentials_provider="moodle",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Получить курс по ID",
                    "config": {
                        "course_id": "{$course.id$}",
                        "field": "id"
                    }
                },
                {
                    "title": "Получить курс по короткому имени",
                    "config": {
                        "course_id": "MATH101",
                        "field": "shortname"
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
        
        moodle_url = payload.get("url") or payload.get("moodle_url")
        token = payload.get("token") or payload.get("wstoken") or payload.get("api_key")
        
        if not moodle_url:
            await logger.error(f"Moodle URL not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle URL not found in credentials"
                }
            }
        
        if not token:
            await logger.error(f"Moodle token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle token not found in credentials"
                }
            }
        
        # Получаем параметры из config
        course_id = config.get("course_id")
        field = config.get("field", "id")
        
        if not course_id:
            await logger.error("course_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "course_id is required"
                }
            }
        
        # Убираем слеш в конце URL если есть
        moodle_url = moodle_url.rstrip("/")
        
        # Формируем URL для Moodle Web Services API
        ws_url = f"{moodle_url}/webservice/rest/server.php"
        
        # Параметры для запроса
        params = {
            "wstoken": token,
            "wsfunction": "core_course_get_courses_by_field",
            "moodlewsrestformat": "json",
            "field": field,
            "value": str(course_id)
        }
        
        # ИСПОЛЬЗУЕМ httpx ДЛЯ ПРЯМЫХ ЗАПРОСОВ К MOODLE API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(ws_url, params=params)
                response.raise_for_status()
                result = response.json()
                
                # Moodle API может вернуть исключение в формате JSON
                if isinstance(result, dict) and "exception" in result:
                    error_message = result.get("message", "Unknown Moodle error")
                    error_code = result.get("errorcode", "unknown")
                    await logger.error(f"Moodle API error: {error_code} - {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"Moodle API error: {error_message}",
                            "errorcode": error_code
                        }
                    }
                
                # Проверяем, что курс найден
                if isinstance(result, list) and len(result) > 0:
                    course = result[0]
                    # Возвращаем результат в формате системы
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "id": course.get("id"),
                                "shortname": course.get("shortname"),
                                "fullname": course.get("fullname"),
                                "displayname": course.get("displayname"),
                                "summary": course.get("summary"),
                                "summaryformat": course.get("summaryformat"),
                                "categoryid": course.get("categoryid"),
                                "categoryname": course.get("categoryname"),
                                "format": course.get("format"),
                                "startdate": course.get("startdate"),
                                "enddate": course.get("enddate"),
                                "visible": course.get("visible"),
                                "idnumber": course.get("idnumber"),
                                "timecreated": course.get("timecreated"),
                                "timemodified": course.get("timemodified")
                            }
                        }
                    }
                else:
                    await logger.error(f"Course not found: {course_id}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Course not found with {field}={course_id}"
                        }
                    }
                    
        except httpx.HTTPStatusError as e:
            await logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"HTTP error: {e.response.status_code}"
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

