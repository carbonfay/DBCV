from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class MedicineGetArticlesIntegration(BaseIntegration):
    """Fetch medical articles from PubMed (Entrez esearch + summary) via PubMed API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_articles",
            version="1.0.0",
            name="Medicine Get Medical Articles (PubMed)",
            description="Получить статьи PubMed по ключевым словам через PubMed API",
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
                        "description": "Ключевые слова для поиска по PubMed",
                        "default": "{$user.query$}"
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "description": "Максимальное количество статей",
                        "default": "{$user.limit$}",
                        "minimum": 1,
                        "maximum": 50
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="other",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Пример поиска статей",
                    "config": {"query": "{$user.query$}", "limit": "{$user.limit$}"}
                },
                {
                    "title": "Пример поиска статей",
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
        limit = config.get("limit", 5)

        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                search_resp = await client.get(
                    esearch_url,
                    headers=headers,
                    params={"db": "pubmed", "retmode": "json", "term": query, "retmax": limit},
                )
                if search_resp.status_code != 200:
                    await logger.error(f"PubMed esearch error {search_resp.status_code}: {search_resp.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": search_resp.status_code,
                            "description": search_resp.text
                        }
                    }
                ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
                if not ids:
                    return {"response": {"ok": True, "result": []}}

                summary_resp = await client.get(
                    esummary_url,
                    headers=headers,
                    params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
                )
                if summary_resp.status_code != 200:
                    await logger.error(f"PubMed esummary error {summary_resp.status_code}: {summary_resp.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": summary_resp.status_code,
                            "description": summary_resp.text
                        }
                    }
                return {"response": {"ok": True, "result": summary_resp.json()}}
            except httpx.RequestError as e:
                await logger.error(f"Request error: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": str(e)
                    }
                }
