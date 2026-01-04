from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetDiseaseInfoIntegration(BaseIntegration):
    """Retrieve disease info from WHO ICD API by entity id via WHO ICD API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_disease_info",
            version="1.0.0",
            name="Medicine Get Disease Info (WHO ICD)",
            description="Получить информацию о заболевании по ICD entity id через WHO ICD API (WHO ICD)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["disease_id"],
                "properties": {
                    "disease_id": {
                        "type": "string",
                        "title": "Disease ID",
                        "description": "ICD entity id (например, 12183)",
                        "default": "{$user.disease_id$}"
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="api_key",  # WHO ICD API key
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса болезни",
                    "config": {"disease_id": "{$user.disease_id$}"}
                },
                {
                    "title": "Пример запроса болезни",
                    "config": {"disease_id": "12183"}
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
        disease_id = config.get("disease_id")
        if not disease_id:
            await logger.error("disease_id is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "disease_id is required"
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="medicine",
            strategy="api_key"
        )
        if not creds:
            await logger.error("WHO ICD API key not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "WHO ICD API key not configured"
                }
            }
        payload = creds.get("payload", creds)
        api_token = payload.get("api_token")
        if not api_token:
            await logger.error("api_token is required for WHO ICD API")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_token is required"
                }
            }

        url = f"https://id.who.int/icd/entity/{disease_id}"
        headers = {"Accept": "application/json", "Authorization": f"Bearer {api_token}"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"WHO ICD error {resp.status_code}: {resp.text}")
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

