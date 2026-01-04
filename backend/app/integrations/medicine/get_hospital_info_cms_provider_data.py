from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetHospitalInfoIntegration(BaseIntegration):
    """Retrieve hospital information by ID from CMS provider-data API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_hospital_info",
            version="1.0.0",
            name="Medicine Get Hospital Info (CMS provider-data)",
            description="Получить информацию о больнице по её ID через CMS provider-data API (CMS provider-data)",
            category="medicine",
            # Используем стандартную medicine-иконку (hospital.svg отсутствует в наборе)
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["hospital_id"],
                "properties": {
                    "hospital_id": {
                        "type": "string",
                        "title": "Hospital ID",
                        "description": "Уникальный идентификатор больницы",
                        "default": "{$user.hospital_id$}"
                    }
                }
            },
            credentials_provider="medicine",  # бесплатный публичный API, ключ не требуется
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса информации о больнице",
                    "config": {
                        "hospital_id": "{$user.hospital_id$}"
                    }
                },
                {
                    "title": "Пример запроса информации о больнице",
                    "config": {
                        "hospital_id": "230012"  # Provider ID (CCN)
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
        hospital_id = config.get("hospital_id")
        if not hospital_id:
            await logger.error("hospital_id is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "hospital_id is required"
                }
            }

        # Публичный источник: CMS provider-data API (hospital general info)
        url = "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0"
        headers = {"Accept": "application/json"}
        payload = {
            "filter": [{"column": "provider_id", "operator": "eq", "value": hospital_id}],
            "includeTotal": True,
            "limit": 1,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results") if isinstance(data, dict) else data
                    if not results:
                        await logger.error("Hospital not found")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 404,
                                "description": "Hospital not found"
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
