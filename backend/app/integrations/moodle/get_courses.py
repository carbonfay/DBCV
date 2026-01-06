from typing import Any, Dict
from uuid import UUID
import httpx
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

class MoodleGetCoursesIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="moodle_get_courses",
            name="Moodle Get Courses",
            description="Получение списка курсов из Moodle",
            version="1.0.0",
            category="education",
            icon_s3_key="icons/integrations/moodle.svg",
            color="#f98012",  # Оранжевый цвет Moodle
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
                    }
                },
                "required": ["moodle_url"]
            }
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        
        # Получаем токен
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

        # Moodle API endpoint
        api_url = f"{base_url}/webservice/rest/server.php"
        
        params = {
            "wstoken": token,
            "wsfunction": "core_course_get_courses",
            "moodlewsrestformat": "json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Moodle иногда возвращает 200, но внутри JSON ошибка
                        if isinstance(data, dict) and "exception" in data:
                             return {
                                "response": {
                                    "ok": False,
                                    "error_code": 400,
                                    "description": f"Moodle Error: {data.get('message')}"
                                }
                            }
                        
                        return {
                            "response": {
                                "ok": True,
                                "result": {"courses": data}
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