"""Moodle Get Courses интеграция используя httpx для прямых запросов к Moodle Web Services API."""
from typing import Dict, Any, List, Optional
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MoodleGetCoursesIntegration(BaseIntegration):
    """Интеграция для получения списка курсов из Moodle через Web Services API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_courses",
            version="1.0.0",
            name="Moodle Get Courses",
            description="Получение списка курсов из Moodle. Можно получить все курсы или отфильтровать по ID",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#f98012",
            config_schema={
                "type": "object",
                "required": [],
                "properties": {
                    "course_ids": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        },
                        "title": "Course IDs",
                        "description": "Массив ID курсов для фильтрации. Если не указан, возвращаются все курсы"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Получить все курсы",
                    "config": {}
                },
                {
                    "title": "Получить курсы по ID",
                    "config": {
                        "course_ids": [1, 2, 5]
                    }
                },
                {
                    "title": "Получить один курс по ID",
                    "config": {
                        "course_ids": [5]
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
        course_ids = config.get("course_ids", [])
        
        # Валидация course_ids если указан
        if course_ids:
            if not isinstance(course_ids, list):
                await logger.error("course_ids must be an array")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "course_ids must be an array of integers"
                    }
                }
            
            # Проверяем, что все элементы - числа
            try:
                course_ids = [int(cid) for cid in course_ids]
            except (ValueError, TypeError):
                await logger.error("course_ids must contain only integers")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "course_ids must contain only integers"
                    }
                }
        
        # Формируем URL для Moodle Web Services API
        # Убираем trailing slash если есть
        moodle_url = moodle_url.rstrip("/")
        api_url = f"{moodle_url}/webservice/rest/server.php"
        
        # Параметры для Moodle REST API
        params = {
            "wstoken": token,
            "wsfunction": "core_course_get_courses",
            "moodlewsrestformat": "json"
        }
        
        # Добавляем фильтр по ID курсов, если указан
        if course_ids:
            for idx, course_id in enumerate(course_ids):
                params[f"options[ids][{idx}]"] = course_id
        
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

