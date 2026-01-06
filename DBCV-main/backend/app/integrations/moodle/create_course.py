from typing import Any, Dict
from uuid import UUID
import httpx
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

class MoodleCreateCourseIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_create_course",
            name="Moodle Create Course",
            description="Создание нового курса в Moodle",
            version="1.0.0",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#f98012",
            credentials_provider="moodle",
            credentials_strategy="api_key",
            library_name="httpx",
            config_schema={
                "type": "object",
                "properties": {
                    "moodle_url": {
                        "type": "string",
                        "title": "Moodle URL",
                        "description": "Адрес вашего Moodle (например, https://school.example.com)"
                    },
                    "fullname": {
                        "type": "string",
                        "title": "Full Name",
                        "description": "Полное название курса"
                    },
                    "shortname": {
                        "type": "string",
                        "title": "Short Name",
                        "description": "Короткое название (должно быть уникальным)"
                    },
                    "categoryid": {
                        "type": "integer",
                        "title": "Category ID",
                        "default": 1,
                        "description": "ID категории (по умолчанию 1)"
                    }
                },
                "required": ["moodle_url", "fullname", "shortname"]
            }
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="moodle",
            strategy="api_key"
        )

        if not creds:
            return {"response": {"ok": False, "error_code": 401, "description": "Moodle credentials not found"}}

        payload_creds = creds.get("payload", creds)
        token = payload_creds.get("api_key") or payload_creds.get("token")

        if not token:
            return {"response": {"ok": False, "error_code": 401, "description": "Moodle token missing"}}

        base_url = config.get("moodle_url", "").rstrip("/")
        if not base_url:
             return {"response": {"ok": False, "error_code": 400, "description": "Moodle URL is required"}}

        api_url = f"{base_url}/webservice/rest/server.php"
        
        # Параметры для создания курса
        params = {
            "wstoken": token,
            "wsfunction": "core_course_create_courses",
            "moodlewsrestformat": "json"
        }
        
        # Moodle требует параметры в формате курсов[0][fullname] и т.д.
        # Но через httpx проще отправить как form-data или query params
        data = {
            "courses[0][fullname]": config["fullname"],
            "courses[0][shortname]": config["shortname"],
            "courses[0][categoryid]": config.get("categoryid", 1),
            "courses[0][format]": "topics"
        }

        try:
            async with httpx.AsyncClient() as client:
                # Используем POST для создания
                response = await client.post(api_url, params=params, data=data, timeout=10.0)
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        # Проверка на ошибку внутри JSON (Moodle style)
                        if isinstance(result, dict) and "exception" in result:
                             return {
                                "response": {
                                    "ok": False,
                                    "error_code": 400,
                                    "description": f"Moodle Error: {result.get('message')}"
                                }
                            }
                        
                        # Успех: возвращается массив созданных курсов
                        return {
                            "response": {
                                "ok": True,
                                "result": {"created_courses": result}
                            }
                        }
                    except Exception:
                         return {
                            "response": {
                                "ok": False,
                                "error_code": 500,
                                "description": "Failed to parse Moodle response"
                            }
                        }
                else:
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": response.text
                        }
                    }
        except Exception as e:
            return {"response": {"ok": False, "error_code": 500, "description": f"Internal error: {str(e)}"}}