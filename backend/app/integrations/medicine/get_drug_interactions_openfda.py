from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetDrugInteractionsIntegration(BaseIntegration):
    """Retrieve drug interaction information by drug ID via openFDA API."""

    @property
    def metadata(self) -> IntegrationMetadata:  # noqa: D401
        return IntegrationMetadata(
            id="medicine_get_drug_interactions",
            version="1.0.0",
            name="Medicine Get Drug Interactions (openFDA)",
            description="Получить информацию о взаимодействиях лекарства по его ID через openFDA API (openFDA)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine/pills.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["drug_id"],
                "properties": {
                    "drug_id": {
                        "type": "string",
                        "title": "Drug ID",
                        "description": "Уникальный идентификатор лекарства",
                        "default": "{$user.drug_id$}"
                    }
                }
            },
            # Публичный openFDA drug label API, ключ не требуется
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример запроса взаимодействий лекарства",
                    "config": {
                        "drug_id": "{$user.drug_id$}"
                    }
                },
                {
                    "title": "Пример запроса взаимодействий лекарства",
                    "config": {
                        "drug_id": "ibuprofen"  # имя действующего вещества
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
        drug_id: str | None = config.get("drug_id")
        if not drug_id:
            await logger.error("drug_id is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "drug_id is required",
                }
            }

        # openFDA drug label: поле drug_interactions содержит текстовые описания
        url = "https://api.fda.gov/drug/label.json"
        headers = {"Accept": "application/json"}
        params = {
            "search": f"drug_interactions:{drug_id}",
            "limit": 5,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    return {
                        "response": {
                            "ok": True,
                            "result": resp.json(),
                        }
                    }
                await logger.error(f"Medicine API error {resp.status_code}: {resp.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": resp.status_code,
                        "description": resp.text,
                    }
                }
            except httpx.RequestError as exc:
                await logger.error(f"Request error: {exc}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": str(exc),
                    }
                }