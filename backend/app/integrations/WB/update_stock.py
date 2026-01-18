"""Wildberries Update Stock integration using httpx."""
import os
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class WBUpdateStockIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="WB_update_stock",
            version="1.0.0",
            name="Wildberries Update Stock",
            description="Update stocks in Wildberries supplier API.",
            category="ecommerce",
            icon_s3_key="icons/integrations/wb.svg",
            color="#00a650",
            config_schema={
                "type": "object",
                "required": ["warehouse_id", "stocks"],
                "properties": {
                    "warehouse_id": {
                        "type": "integer",
                        "title": "Warehouse ID",
                        "description": "Wildberries warehouse ID."
                    },
                    "stocks": {
                        "type": "array",
                        "title": "Stocks",
                        "description": "List of stock updates.",
                        "items": {
                            "type": "object",
                            "required": ["sku", "amount"],
                            "properties": {
                                "sku": {
                                    "type": "string",
                                    "title": "SKU",
                                    "description": "Product SKU or barcode."
                                },
                                "amount": {
                                    "type": "integer",
                                    "title": "Amount",
                                    "description": "Stock amount."
                                }
                            }
                        }
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Update stock for two items",
                    "config": {
                        "warehouse_id": 12345,
                        "stocks": [
                            {"sku": "1234567890", "amount": 10},
                            {"sku": "0987654321", "amount": 0}
                        ]
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
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        if not creds:
            await logger.error("Wildberries credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Wildberries API key not found in credentials"
                }
            }

        payload = creds.get("payload", {}) or creds
        api_key = payload.get("api_key") or payload.get("token") or payload.get("key")
        if not api_key:
            await logger.error("API key not found in credentials payload")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Wildberries API key not found in credentials"
                }
            }

        warehouse_id = config.get("warehouse_id")
        stocks = config.get("stocks")
        if warehouse_id is None or not stocks:
            await logger.error("warehouse_id and stocks are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "warehouse_id and stocks are required"
                }
            }

        base_url = os.getenv("WB_API_BASE_URL", "https://openapi.wildberries.ru")
        path = os.getenv("WB_UPDATE_STOCK_PATH", "/api/v3/stocks/{warehouseId}")
        url = f"{base_url}{path}".format(warehouseId=int(warehouse_id))
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        body = {"stocks": stocks}

        try:
            # Force IPv4 to avoid "no usable address" errors in some environments.
            transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
            async with httpx.AsyncClient(timeout=30.0, transport=transport) as client:
                response = await client.put(url, headers=headers, json=body)
                response.raise_for_status()
                try:
                    result = response.json()
                except ValueError:
                    result = {"raw": response.text}

            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except httpx.HTTPStatusError as e:
            await logger.error(f"Wildberries API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": e.response.text
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
