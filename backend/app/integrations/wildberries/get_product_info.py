"""Wildberries Get Product Info integration.

Calls Wildberries API endpoint GET /content/v1/cards/filter
using `httpx` AsyncClient.
"""
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False


class WildberriesGetProductInfoIntegration(BaseIntegration):
    """Интеграция для получения информации о товарах Wildberries."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="wildberries_get_product_info",
            version="1.0.0",
            name="Wildberries Get Product Info",
            description="Получение информации о товарах через Wildberries API (GET /content/v1/cards/filter)",
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#ff6600",
            config_schema={
                "type": "object",
                "required": [],
                "properties": {
                    "base_url": {
                        "type": "string",
                        "title": "Base URL",
                        "description": "Базовый URL Wildberries API",
                        "default": "https://suppliers-api.wildberries.ru"
                    },
                    "params": {
                        "type": "object",
                        "title": "Query params",
                        "description": "Словарь query-параметров, передающихся в GET /content/v1/cards/filter"
                    }
                }
            },
            credentials_provider="wildberries",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Пример: найти карточки по фильтру",
                    "config": {
                        "base_url": "https://suppliers-api.wildberries.ru",
                        "params": {"query": "iphone"}
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {"response": {"ok": False, "error_code": 500, "description": "httpx is not installed"}}

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="wildberries", strategy="api_key"
        )

        # Build payload / headers
        headers = {}
        if creds:
            payload = creds.get("payload", {}) or creds
            api_key = payload.get("api_key") or payload.get("token") or payload.get("key")
            if api_key:
                # Wildberries sometimes expects X-API-KEY or Authorization header depending on integration
                headers["X-API-KEY"] = str(api_key)
                headers.setdefault("Authorization", f"Bearer {api_key}")
        else:
            await logger.info("No Wildberries credentials found; calling endpoint without API key header")

        base_url = config.get("base_url") or "https://suppliers-api.wildberries.ru"
        params = config.get("params") or {}

        url = f"{base_url.rstrip('/')}/content/v1/cards/filter"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params, headers=headers)

            # Try parse JSON
            try:
                data = resp.json()
            except Exception:
                data = {"text": resp.text}

            if resp.status_code >= 200 and resp.status_code < 300:
                return {"response": {"ok": True, "result": data}}
            else:
                await logger.error(f"Wildberries API returned {resp.status_code}: {resp.text}")
                return {"response": {"ok": False, "error_code": resp.status_code, "description": data}}

        except httpx.HTTPError as e:
            await logger.error(f"HTTP error when calling Wildberries: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
        except Exception as e:
            logging.exception("Unexpected error in Wildberries integration")
            await logger.error(f"Unexpected error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
