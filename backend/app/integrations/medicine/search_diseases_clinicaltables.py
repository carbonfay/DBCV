from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineSearchDiseasesIntegration(BaseIntegration):
    """Search diseases/conditions via ClinicalTables through ClinicalTables API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_search_diseases",
            version="1.0.0",
            name="Medicine Search Diseases (ClinicalTables)",
            description="Поиск заболеваний (conditions) через ClinicalTables (ClinicalTables)",
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
                        "description": "Поисковый запрос по названию заболевания",
                        "default": "{$user.query$}"
                    },
                    "max_results": {
                        "type": "integer",
                        "title": "Max results",
                        "description": "Максимальное количество результатов",
                        "default": "{$user.max_results$}",
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
                    "title": "Пример поиска заболеваний",
                    "config": {"query": "{$user.query$}", "max_results": "{$user.max_results$}"}
                },
                {
                    "title": "Пример поиска заболеваний",
                    "config": {"query": "diabetes", "max_results": 5}
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

        max_results = config.get("max_results", 10)

        url = "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search"
        headers = {"Accept": "application/json"}
        params = {"terms": query, "maxList": max_results}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    return {"response": {"ok": True, "result": resp.json()}}
                await logger.error(f"ClinicalTables error {resp.status_code}: {resp.text}")
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
