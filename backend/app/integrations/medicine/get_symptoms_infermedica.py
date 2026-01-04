from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetSymptomsIntegration(BaseIntegration):
    """Retrieve symptom list via Infermedica API through Infermedica."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_symptoms",
            version="1.0.0",
            name="Medicine Get Symptoms (Infermedica)",
            description="Получить список симптомов через Infermedica API (Infermedica)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "title": "Language",
                        "description": "Код языка, по умолчанию en",
                        "default": "en"
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="api_key",  # app_id + app_key
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса симптомов",
                    "config": {"language": "{$user.language$}"}
                },
                {
                    "title": "Пример запроса симптомов",
                    "config": {"language": "en"}
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
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="medicine",
            strategy="api_key"
        )
        if not creds:
            await logger.error("Infermedica credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Infermedica credentials not configured"
                }
            }

        payload = creds.get("payload", creds)
        app_id: str | None = payload.get("app_id")
        app_key: str | None = payload.get("app_key")
        if not app_id or not app_key:
            await logger.error("app_id and app_key are required for Infermedica")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "app_id and app_key are required"
                }
            }

        language = config.get("language", "en")

        url = "https://api.infermedica.com/v3/symptoms"
        headers = {
            "Accept": "application/json",
            "App-Id": app_id,
            "App-Key": app_key,
            "Content-Type": "application/json",
        }
        params = {"language": language}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"Infermedica error {resp.status_code}: {resp.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": resp.status_code,
                        "description": resp.text
                    }
                }
            except httpx.RequestError as e:
                await logger.error(f"Request error: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": str(e)
                    }
                }

