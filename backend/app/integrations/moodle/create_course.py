"""Moodle Create Course интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class MoodleCreateCourseIntegration(BaseIntegration):
    """Интеграция для создания курса в Moodle."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_create_course",
            version="1.0.0",
            name="Moodle Create Course",
            description="Создание курса в Moodle через Moodle Web Services API",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#FFCC00",
            config_schema={
                "type": "object",
                "required": ["course_data"],
                "properties": {
                    "course_data": {
                        "type": "object",
                        "title": "Course Data",
                        "description": "Данные курса для создания",
                        "required": ["fullname", "shortname"],
                        "properties": {
                            "fullname": {
                                "type": "string",
                                "title": "Full Name",
                                "description": "Полное название курса"
                            },
                            "shortname": {
                                "type": "string",
                                "title": "Short Name",
                                "description": "Краткое название курса (должно быть уникальным)"
                            },
                            "categoryid": {
                                "type": "integer",
                                "title": "Category ID",
                                "description": "ID категории курса",
                                "default": 1
                            },
                            "summary": {
                                "type": "string",
                                "title": "Summary",
                                "description": "Описание курса"
                            },
                            "format": {
                                "type": "string",
                                "title": "Format",
                                "description": "Формат курса",
                                "enum": ["topics", "weeks", "social", "site", "scorm", "resource", "activity"],
                                "default": "topics"
                            },
                            "startdate": {
                                "type": "integer",
                                "title": "Start Date",
                                "description": "Дата начала (Unix timestamp)"
                            },
                            "enddate": {
                                "type": "integer",
                                "title": "End Date",
                                "description": "Дата окончания (Unix timestamp)"
                            },
                            "numsections": {
                                "type": "integer",
                                "title": "Number of Sections",
                                "description": "Количество секций в курсе",
                                "default": 1
                            },
                            "showgrades": {
                                "type": "integer",
                                "title": "Show Grades",
                                "description": "Показывать оценки (1 для да, 0 для нет)",
                                "enum": [0, 1],
                                "default": 1
                            },
                            "newsitems": {
                                "type": "integer",
                                "title": "News Items",
                                "description": "Количество элементов новостей",
                                "default": 5
                            },
                            "maxbytes": {
                                "type": "integer",
                                "title": "Max Bytes",
                                "description": "Максимальный размер файлов в байтах",
                                "default": 104857600  # 100MB
                            },
                            "showreports": {
                                "type": "integer",
                                "title": "Show Reports",
                                "description": "Показывать отчеты (1 для да, 0 для нет)",
                                "enum": [0, 1],
                                "default": 0
                            },
                            "visible": {
                                "type": "integer",
                                "title": "Visible",
                                "description": "Видимость курса (1 для видимого, 0 для скрытого)",
                                "enum": [0, 1],
                                "default": 1
                            }
                        }
                    }
                }
            },
            credentials_provider="moodle",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать базовый курс",
                    "config": {
                        "course_data": {
                            "fullname": "Информатика 101",
                            "shortname": "INF101",
                            "categoryid": 2,
                            "summary": "Введение в основы программирования"
                        }
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
        Выполняет интеграцию используя httpx для прямых вызовов Moodle Web Services API.

        Args:
            config: Параметры интеграции
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
                    "description": "httpx library is not available"
                }
            }

        # Получаем API данные из credentials
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
                    "description": "Moodle credentials not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        # Получаем URL Moodle и токен
        moodle_url = payload.get("moodle_url")
        token = payload.get("token") or payload.get("api_key")

        if not moodle_url or not token:
            await logger.error(f"Moodle URL or token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Moodle URL and token are required"
                }
            }

        # Получаем данные курса из config
        course_data = config.get("course_data")

        if not course_data or not isinstance(course_data, dict):
            await logger.error("course_data is required and must be a dictionary")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "course_data is required and must be a dictionary"
                }
            }

        # Проверяем обязательные поля
        if "fullname" not in course_data or "shortname" not in course_data:
            await logger.error("fullname and shortname are required in course_data")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "fullname and shortname are required in course_data"
                }
            }

        # Подготавливаем параметры для API запроса
        params = {
            'wstoken': token,
            'wsfunction': 'core_course_create_courses',
            'moodlewsrestformat': 'json'
        }

        # Добавляем параметры курса к запросу
        for key, value in course_data.items():
            # Moodle API ожидает параметры в формате "courses[0][property]"
            if isinstance(value, bool):
                value = 1 if value else 0
            params[f'courses[0][{key}]'] = value

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # Проверяем, что URL имеет правильный формат
            if not moodle_url.endswith('/'):
                moodle_url += '/'
            
            api_url = f"{moodle_url}webservice/rest/server.php"

            # Выполняем POST-запрос к Moodle API
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, data=params)

            # Проверяем статус ответа
            if response.status_code != 200:
                await logger.error(f"Moodle API returned status {response.status_code}: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"Moodle API returned status {response.status_code}: {response.text}"
                    }
                }

            # Парсим JSON-ответ
            try:
                data = response.json()
            except json.JSONDecodeError:
                await logger.error(f"Invalid JSON response from Moodle API: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": f"Invalid JSON response from Moodle API: {response.text}"
                    }
                }

            # Проверяем, есть ли ошибки в ответе Moodle
            if isinstance(data, dict) and 'exception' in data:
                await logger.error(f"Moodle API error: {data}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": f"Moodle API error: {data.get('message', 'Unknown error')}"
                    }
                }

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "courses": data if isinstance(data, list) else [data],
                        "created": True
                    }
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP request error: {e}"
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

