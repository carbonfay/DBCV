from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineSearchDrugsIntegration(BaseIntegration):
    """Search drugs via RxNav API.

    Выполняет поиск лекарственных средств по названию через RxNav REST API.
    """

    @property
    def metadata(self) -> IntegrationMetadata:  # noqa: D401
        return IntegrationMetadata(
            id="medicine_search_drugs",
            version="1.0.0",
            name="Medicine Search Drugs (RxNav)",
            description="Поиск лекарств по названию через RxNav API (RxNav)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine/pills.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "title": "Search query",
                        "description": "Поисковый запрос (название лекарства)",
                        "default": "{$user.query$}"
                    }
                }
            },
            # Бесплатный публичный API RxNav, ключ не требуется
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример поиска лекарств",
                    "config": {
                        "query": "{$user.query$}"
                    }
                },
                {
                    "title": "Пример поиска лекарств",
                    "config": {
                        "query": "ibuprofen"
                    }
                },
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        query: str | None = config.get("query")
        if not query:
            await logger.error("query is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "query is required",
                }
            }

        # Публичный RxNav API
        url = "https://rxnav.nlm.nih.gov/REST/drugs.json"
        headers = {"Accept": "application/json"}
        params = {"name": query}

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