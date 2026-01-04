from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetICD10Integration(BaseIntegration):
    """Retrieve ICD-10 details via ClinicalTables icd10cm API through ClinicalTables."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_icd10",
            version="1.0.0",
            name="Medicine Get ICD-10 Code (ClinicalTables)",
            description="Получить информацию о коде ICD-10 через ClinicalTables icd10cm (ClinicalTables)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {
                        "type": "string",
                        "title": "ICD-10 code",
                        "description": "Код ICD-10 (например, E11.9)",
                        "default": "{$user.code$}"
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса кода ICD-10",
                    "config": {"code": "{$user.code$}"}
                },
                {
                    "title": "Пример запроса кода ICD-10",
                    "config": {"code": "E11.9"}
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
        code = config.get("code")
        if not code:
            await logger.error("code is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "code is required"
                }
            }

        url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
        headers = {"Accept": "application/json"}
        params = {"terms": code, "maxList": 1}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"ClinicalTables icd10cm error {resp.status_code}: {resp.text}")
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
