from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetTrialsIntegration(BaseIntegration):
    """Fetch clinical trials from ClinicalTrials.gov via ClinicalTrials.gov API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_trials",
            version="1.0.0",
            name="Medicine Get Clinical Trials (ClinicalTrials.gov)",
            description="Получить список клинических исследований через ClinicalTrials.gov (ClinicalTrials.gov)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "title": "Search query",
                        "description": "Ключевые слова для поиска по ClinicalTrials.gov",
                        "default": "{$user.query$}"
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "description": "Максимальное количество записей",
                        "default": "{$user.limit$}",
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример поиска клинических исследований",
                    "config": {"query": "{$user.query$}", "limit": "{$user.limit$}"}
                },
                {
                    "title": "Пример поиска клинических исследований",
                    "config": {"query": "diabetes", "limit": 5}
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
        query = config.get("query")
        if not query:
            await logger.error("query is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "query is required"
                }
            }
        limit = config.get("limit", 10)

        url = "https://clinicaltrials.gov/api/v2/studies"
        headers = {"Accept": "application/json"}
        params = {
            "format": "json",
            "query.term": query,
            "pageSize": limit,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"ClinicalTrials.gov error {resp.status_code}: {resp.text}")
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
