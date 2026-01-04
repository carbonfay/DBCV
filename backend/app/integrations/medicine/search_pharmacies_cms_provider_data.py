from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineSearchPharmaciesIntegration(BaseIntegration):
    """Search pharmacies via CMS provider-data API through CMS provider-data."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_search_pharmacies",
            version="1.0.0",
            name="Medicine Search Pharmacies (CMS provider-data)",
            description="Поиск аптек через CMS provider-data API (CMS provider-data)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "title": "Query",
                        "description": "Название аптеки (частичное совпадение)",
                        "default": "{$user.query$}"
                    },
                    "state": {
                        "type": "string",
                        "title": "State (optional)",
                        "description": "Двухбуквенный код штата",
                        "default": "{$user.state$}",
                        "minLength": 2,
                        "maxLength": 2
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "description": "Максимум результатов",
                        "default": "{$user.limit$}",
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            },
            # CMS provider-data API: бесплатный X-App-Token (рекомендуется для повышения лимитов)
            # Документация: https://data.cms.gov/provider-data/api/1?authentication=false
            credentials_provider="medicine",
            credentials_strategy="api_key",  # X-App-Token
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример поиска аптеки",
                    "config": {"query": "{$user.query$}", "state": "{$user.state$}", "limit": "{$user.limit$}"}
                },
                {
                    "title": "Пример поиска аптеки",
                    "config": {"query": "CVS", "state": "TX", "limit": 5}
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
            await logger.error("Medicine API credentials (app_token) not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Medicine credentials not configured"
                }
            }

        payload = creds.get("payload", creds)
        app_token: str | None = payload.get("app_token")
        if not app_token:
            await logger.error("app_token is required for CMS Socrata")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "app_token is required"
                }
            }

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
        state = config.get("state")
        limit = config.get("limit", 10)

        url = "https://data.cms.gov/provider-data/api/1/datastore/query/ynj2-r877/0"
        headers = {"Accept": "application/json", "X-App-Token": app_token}
        filters = [{"column": "provider_name", "operator": "contains", "value": query}]
        if state:
            filters.append({"column": "state", "operator": "eq", "value": state.upper()})
        payload_query = {
            "filter": filters,
            "includeTotal": True,
            "limit": limit,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload_query)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    return {"response": {"ok": True, "result": results}}
                await logger.error(f"CMS Socrata error {resp.status_code}: {resp.text}")
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
