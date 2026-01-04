from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetDrugInfoIntegration(BaseIntegration):
    """Retrieve drug information from RxNav by RXCUI or name via RxNav API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_drug_info",
            version="1.0.0",
            name="Medicine Get Drug Info (RxNav)",
            description="Получить информацию о лекарстве по RXCUI или названию через RxNav (RxNav)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["drug_id"],
                "properties": {
                    "drug_id": {
                        "type": "string",
                        "title": "Drug ID (RXCUI or name)",
                        "description": "RXCUI или название препарата",
                        "default": "{$user.drug_id$}"
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса информации о лекарстве",
                    "config": {"drug_id": "{$user.drug_id$}"}
                },
                {
                    "title": "Пример запроса информации о лекарстве",
                    "config": {"drug_id": "1191"}
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
        drug_id = config.get("drug_id")
        if not drug_id:
            await logger.error("drug_id is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "drug_id is required"
                }
            }

        # RxNav allows name or RXCUI via allProperties
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{drug_id}/allProperties.json"
        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"RxNav error {resp.status_code}: {resp.text}")
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
