"""Moodle Get Courses интеграция используя httpx для Moodle REST API."""
from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MoodleGetCoursesIntegration(BaseIntegration):
    """Интеграция для получения списка курсов из Moodle через REST API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_courses",
            version="1.0.0",
            name="Moodle Get Courses",
            description="Получить список курсов из Moodle через REST API",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#f98012",
            config_schema={
                "type": "object",
                "properties": {}
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Получить все курсы",
                    "config": {}
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
        Выполняет интеграцию используя httpx для прямых запросов к Moodle REST API.
        
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
        
        # Получаем URL Moodle и токен из credentials
        moodle_url = payload.get("url") or payload.get("moodle_url")
        api_key = payload.get("api_key") or payload.get("token") or payload.get("wstoken")
        
        if not moodle_url:
            await logger.error("moodle_url not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "moodle_url not found in credentials. Please provide 'url' or 'moodle_url' in credentials"
                }
            }
        
        if not api_key:
            await logger.error("api_key not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials. Please provide 'api_key', 'token', or 'wstoken' in credentials"
                }
            }
        
        # Убеждаемся, что URL не заканчивается на слэш
        moodle_url = moodle_url.rstrip("/")
        
        # Формируем URL для Moodle REST API
        rest_url = f"{moodle_url}/webservice/rest/server.php"
        
        # Формируем параметры запроса
        # core_course_get_courses возвращает все курсы, к которым у пользователя есть доступ
        params = {
            "wstoken": api_key,
            "wsfunction": "core_course_get_courses",
            "moodlewsrestformat": "json"
        }
        
        # ИСПОЛЬЗУЕМ httpx ДЛЯ ПРЯМЫХ ЗАПРОСОВ К MOODLE REST API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(rest_url, params=params)
                response.raise_for_status()
                
                result = response.json()
                
                # Проверяем наличие ошибок в ответе Moodle
                if isinstance(result, dict) and "exception" in result:
                    error_message = result.get("message", "Unknown Moodle API error")
                    await logger.error(f"Moodle API error: {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": result.get("errorcode", 500),
                            "description": error_message
                        }
                    }
                
                # Если result - это список курсов, возвращаем его
                if isinstance(result, list):
                    courses = result
                elif isinstance(result, dict) and "courses" in result:
                    courses = result["courses"]
                else:
                    courses = result
                
                # Возвращаем результат в формате системы
                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "courses": courses,
                            "count": len(courses) if isinstance(courses, list) else 1
                        }
                    }
                }
        except httpx.HTTPStatusError as e:
            await logger.error(f"Moodle HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"Moodle API HTTP error: {e.response.status_code}"
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"Moodle request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Failed to connect to Moodle: {str(e)}"
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

