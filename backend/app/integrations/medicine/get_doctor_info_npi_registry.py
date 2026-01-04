from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetDoctorInfoIntegration(BaseIntegration):
    """Retrieve doctor info by NPI via NPI Registry API through NPI Registry."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_doctor_info",
            version="1.0.0",
            name="Medicine Get Doctor Info (NPI Registry)",
            description="Получить информацию о докторе по NPI через NPI Registry (NPI Registry)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["npi"],
                "properties": {
                    "npi": {
                        "type": "string",
                        "title": "NPI",
                        "description": "National Provider Identifier (10 digits)",
                        "default": "{$user.npi$}"
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса доктора",
                    "config": {"npi": "{$user.npi$}"}
                },
                {
                    "title": "Пример запроса доктора",
                    "config": {"npi": "1234567890"}
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
        npi = config.get("npi")
        if not npi:
            await logger.error("npi is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "npi is required"
                }
            }

        url = "https://npiregistry.cms.hhs.gov/api/"
        headers = {"Accept": "application/json"}
        params = {"number": npi, "version": "2.1"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"NPI Registry error {resp.status_code}: {resp.text}")
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
