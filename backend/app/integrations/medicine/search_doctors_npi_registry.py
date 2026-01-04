from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineSearchDoctorsIntegration(BaseIntegration):
    """Search doctors via NPI Registry API through NPI Registry."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_search_doctors",
            version="1.0.0",
            name="Medicine Search Doctors (NPI Registry)",
            description="Поиск докторов через NPI Registry (по имени/городу/штату) (NPI Registry)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["first_name", "last_name"],
                "properties": {
                    "first_name": {
                        "type": "string",
                        "title": "First name",
                        "description": "Имя доктора",
                        "default": "{$user.first_name$}"
                    },
                    "last_name": {
                        "type": "string",
                        "title": "Last name",
                        "description": "Фамилия доктора",
                        "default": "{$user.last_name$}"
                    },
                    "city": {
                        "type": "string",
                        "title": "City",
                        "description": "Город (опционально)"
                    },
                    "state": {
                        "type": "string",
                        "title": "State",
                        "description": "Двухбуквенный код штата (опционально)",
                        "default": "{$user.state$}",
                        "minLength": 2,
                        "maxLength": 2
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
                    "title": "Пример поиска доктора",
                    "config": {"first_name": "{$user.first_name$}", "last_name": "{$user.last_name$}", "state": "{$user.state$}", "limit": "{$user.limit$}"}
                },
                {
                    "title": "Пример поиска доктора",
                    "config": {"first_name": "John", "last_name": "Smith", "state": "TX", "limit": 5}
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
        first_name = config.get("first_name")
        last_name = config.get("last_name")
        if not first_name or not last_name:
            await logger.error("first_name and last_name are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "first_name and last_name are required"
                }
            }
        city = config.get("city")
        state = config.get("state")
        limit = config.get("limit", 10)

        url = "https://npiregistry.cms.hhs.gov/api/"
        headers = {"Accept": "application/json"}
        params = {
            "first_name": first_name,
            "last_name": last_name,
            "version": "2.1",
            "limit": limit,
        }
        if city:
            params["city"] = city
        if state:
            params["state"] = state.upper()

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
