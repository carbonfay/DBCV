"""Moodle Create Course интеграция используя httpx для прямых запросов к Moodle Web Services API."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
import httpx


class MoodleCreateCourseIntegration(BaseIntegration):
    """Интеграция для создания курса в Moodle через Web Services API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_create_course",
            version="1.0.0",
            name="Moodle Create Course",
            description="Создание нового курса в Moodle через Web Services API",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#f98012",
            config_schema={
                "type": "object",
                "required": ["fullname", "shortname", "categoryid"],
                "properties": {
                    "fullname": {
                        "type": "string",
                        "title": "Full Name",
                        "description": "Полное название курса"
                    },
                    "shortname": {
                        "type": "string",
                        "title": "Short Name",
                        "description": "Краткое название курса (уникальное)"
                    },
                    "categoryid": {
                        "type": "integer",
                        "title": "Category ID",
                        "description": "ID категории, в которую будет добавлен курс"
                    },
                    "summary": {
                        "type": "string",
                        "title": "Summary",
                        "description": "Описание курса (HTML поддерживается)",
                        "default": ""
                    },
                    "summaryformat": {
                        "type": "integer",
                        "title": "Summary Format",
                        "description": "Формат описания: 0=MOODLE, 1=HTML, 2=PLAIN, 4=MARKDOWN",
                        "enum": [0, 1, 2, 4],
                        "default": 1
                    },
                    "format": {
                        "type": "string",
                        "title": "Course Format",
                        "description": "Формат курса",
                        "enum": ["topics", "weeks", "social", "singleactivity"],
                        "default": "topics"
                    },
                    "startdate": {
                        "type": "integer",
                        "title": "Start Date",
                        "description": "Дата начала курса (UNIX timestamp). Если не указана, используется текущая дата"
                    },
                    "enddate": {
                        "type": "integer",
                        "title": "End Date",
                        "description": "Дата окончания курса (UNIX timestamp)"
                    },
                    "visible": {
                        "type": "integer",
                        "title": "Visible",
                        "description": "Видимость курса: 0=скрыт, 1=видим",
                        "enum": [0, 1],
                        "default": 1
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык курса (например, 'ru', 'en')"
                    },
                    "numsections": {
                        "type": "integer",
                        "title": "Number of Sections",
                        "description": "Количество разделов (для форматов topics и weeks)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Простой курс",
                    "config": {
                        "fullname": "Введение в Python",
                        "shortname": "python101",
                        "categoryid": 1,
                        "summary": "Базовый курс по программированию на Python",
                        "format": "topics",
                        "visible": 1
                    }
                },
                {
                    "title": "Курс с датами",
                    "config": {
                        "fullname": "Продвинутый Python",
                        "shortname": "python201",
                        "categoryid": 1,
                        "summary": "Продвинутый курс по Python",
                        "format": "weeks",
                        "startdate": 1704067200,
                        "enddate": 1735689600,
                        "numsections": 12,
                        "visible": 1
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
                    "description": "Moodle credentials not found. Please configure API key and Moodle URL."
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        # Получаем API ключ и URL Moodle
        api_key = payload.get("api_key") or payload.get("token") or payload.get("wstoken")
        moodle_url = payload.get("moodle_url") or payload.get("url") or payload.get("base_url")
        
        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key (wstoken) not found in credentials"
                }
            }
        
        if not moodle_url:
            await logger.error(f"Moodle URL not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle URL not found in credentials"
                }
            }
        
        # Нормализуем URL (убираем trailing slash, добавляем путь к Web Services)
        moodle_url = moodle_url.rstrip("/")
        if not moodle_url.endswith("/webservice/rest/server.php"):
            if moodle_url.endswith("/webservice/rest"):
                moodle_url = moodle_url + "/server.php"
            elif moodle_url.endswith("/webservice"):
                moodle_url = moodle_url + "/rest/server.php"
            else:
                moodle_url = moodle_url + "/webservice/rest/server.php"
        
        # Получаем параметры из config
        fullname = config.get("fullname")
        shortname = config.get("shortname")
        categoryid = config.get("categoryid")
        
        if not fullname or not shortname or categoryid is None:
            await logger.error("fullname, shortname and categoryid are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "fullname, shortname and categoryid are required"
                }
            }
        
        # Формируем параметры для Moodle API
        # Moodle Web Services API использует формат courses[0][fieldname] для массивов
        params = {
            "wstoken": api_key,
            "wsfunction": "core_course_create_courses",
            "moodlewsrestformat": "json"
        }
        
        # Собираем данные курса
        course_data = {
            "fullname": str(fullname),
            "shortname": str(shortname),
            "categoryid": int(categoryid)
        }
        
        # Добавляем опциональные параметры
        if "summary" in config:
            course_data["summary"] = str(config["summary"])
        
        if "summaryformat" in config:
            course_data["summaryformat"] = int(config["summaryformat"])
        
        if "format" in config:
            course_data["format"] = str(config["format"])
        
        if "startdate" in config:
            course_data["startdate"] = int(config["startdate"])
        
        if "enddate" in config:
            course_data["enddate"] = int(config["enddate"])
        
        if "visible" in config:
            course_data["visible"] = int(config["visible"])
        
        if "lang" in config:
            course_data["lang"] = str(config["lang"])
        
        if "numsections" in config:
            course_data["numsections"] = int(config["numsections"])
        
        # Преобразуем в формат Moodle API (courses[0][fieldname])
        for key, value in course_data.items():
            params[f"courses[0][{key}]"] = value
        
        # ИСПОЛЬЗУЕМ httpx ДЛЯ ПРЯМЫХ ЗАПРОСОВ К MOODLE API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(moodle_url, data=params)
                response.raise_for_status()
                result = response.json()
                
                # Moodle API возвращает результат в формате:
                # {"id": course_id} при успехе или {"exception": "...", "errorcode": "...", "message": "..."} при ошибке
                if "exception" in result:
                    error_code = result.get("errorcode", "MOODLE_ERROR")
                    error_message = result.get("message", result.get("exception", "Unknown error"))
                    await logger.error(f"Moodle API error: {error_code} - {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": f"Moodle API error: {error_message}",
                            "moodle_error_code": error_code
                        }
                    }
                
                # Проверяем, что курс был создан
                if "id" in result or (isinstance(result, list) and len(result) > 0 and "id" in result[0]):
                    course_id = result.get("id") if isinstance(result, dict) else result[0].get("id")
                    await logger.info(f"Course created successfully with ID: {course_id}")
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "course_id": course_id,
                                "fullname": fullname,
                                "shortname": shortname,
                                "categoryid": categoryid
                            }
                        }
                    }
                else:
                    await logger.error(f"Unexpected Moodle API response: {result}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": f"Unexpected Moodle API response format: {result}"
                        }
                    }
                    
        except httpx.HTTPStatusError as e:
            await logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"HTTP error: {e.response.text[:200]}"
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

