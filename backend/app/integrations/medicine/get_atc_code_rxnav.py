from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetATCCodeIntegration(BaseIntegration):
    """Retrieve ATC code via RxNav property for given RXCUI through RxNav API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_atc_code",
            version="1.0.0",
            name="Medicine Get ATC Code (RxNav)",
            description="Получить ATC-код для RXCUI через RxNav property API (RxNav)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["rxcui"],
                "properties": {
                    "rxcui": {
                        "type": "string",
                        "title": "RXCUI",
                        "description": "Идентификатор RxNorm для препарата",
                        "default": "{$user.rxcui$}"
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса ATC",
                    "config": {"rxcui": "{$user.rxcui$}"}
                },
                {
                    "title": "Пример запроса ATC",
                    "config": {"rxcui": "1191"}
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
        rxcui = config.get("rxcui")
        if not rxcui:
            await logger.error("rxcui is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "rxcui is required"
                }
            }

        url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/property.json"
        headers = {"Accept": "application/json"}
        params = {"propName": "ATC"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"RxNav ATC error {resp.status_code}: {resp.text}")
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

