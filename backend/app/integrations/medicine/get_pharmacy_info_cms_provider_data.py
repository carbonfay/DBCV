from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetPharmacyInfoIntegration(BaseIntegration):
    """Retrieve pharmacy information by NPI from CMS provider-data API through CMS provider-data."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_pharmacy_info",
            version="1.1.0",
            name="Medicine Get Pharmacy Info (CMS provider-data)",
            description="Получить информацию об аптеке по её NPI через CMS provider-data API (POS) (CMS provider-data)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["npi"],
                "properties": {
                    "npi": {
                        "type": "string",
                        "title": "Pharmacy NPI",
                        "description": "National Provider Identifier",
                        "default": "{$user.npi$}"
                    },
                    "state": {
                        "type": "string",
                        "title": "State (optional)",
                        "description": "Двухбуквенный код штата для уточнения поиска",
                        "default": "{$user.state$}",
                        "minLength": 2,
                        "maxLength": 2
                    }
                }
            },
            # CMS provider-data API: бесплатный X-App-Token (рекомендуется для повышения лимитов)
            # Документация: https://data.cms.gov/provider-data/api/1?authentication=false
            credentials_provider="medicine",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса информации об аптеке",
                    "config": {
                        "npi": "{$user.npi$}",
                        "state": "{$user.state$}"
                    }
                },
                {
                    "title": "Пример запроса информации об аптеке",
                    "config": {
                        "npi": "1234567890",
                        "state": "TX"
                    }
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
            await logger.error("Medicine API credentials not found (expected X-App-Token)")
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
            await logger.error("app_token (X-App-Token) missing in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "app_token (X-App-Token) missing in credentials"
                }
            }

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

        state = config.get("state")

        # CMS provider-data API для Provider of Services (POS). Contains pharmacies among providers.
        # Документация: https://data.cms.gov/provider-data/api/1?authentication=false
        url = "https://data.cms.gov/provider-data/api/1/datastore/query/ynj2-r877/0"
        headers = {"Accept": "application/json", "X-App-Token": app_token}
        filters = [{"column": "npi", "operator": "eq", "value": npi}]
        if state:
            filters.append({"column": "state", "operator": "eq", "value": state.upper()})
        payload_query = {
            "filter": filters,
            "includeTotal": True,
            "limit": 1,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload_query)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if not results:
                        await logger.error("Pharmacy not found")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 404,
                                "description": "Pharmacy not found"
                            }
                        }
                    return {
                        "response": {
                            "ok": True,
                            "result": results[0]  # возвращаем первую найденную запись
                        }
                    }
                await logger.error(f"Medicine API error {resp.status_code}: {resp.text}")
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
