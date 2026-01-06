from typing import Any, Dict
from uuid import UUID
import httpx
# Добавляем импорт IntegrationMetadata
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

class OzonGetProductInfoIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        # Оборачиваем в класс IntegrationMetadata
        return IntegrationMetadata(
            id="ozon_get_product_info",
            name="Ozon Get Product Info",
            description="Получение информации о товаре Ozon по ID",
            version="1.0.0",
            category="ecommerce",
            icon_s3_key="icons/integrations/ozon.svg",
            color="#005bff",
            credentials_provider="ozon",
            credentials_strategy="api_key",
            library_name="httpx",
            config_schema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "title": "Product ID",
                        "description": "ID товара в системе Ozon"
                    },
                    "offer_id": {
                        "type": "string",
                        "title": "Offer ID",
                        "description": "Артикул товара"
                    }
                },
                "required": []
            }
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
            provider="ozon",
            strategy="api_key"
        )

        if not creds:
            return {"response": {"ok": False, "error_code": 401, "description": "Ozon credentials not found"}}
        
        payload_creds = creds.get("payload", creds)
        client_id = payload_creds.get("client_id")
        api_key = payload_creds.get("api_key")

        if not client_id or not api_key:
            return {"response": {"ok": False, "error_code": 401, "description": "Client-Id or Api-Key missing"}}

        payload = {}
        if config.get("product_id"): payload["product_id"] = int(config["product_id"])
        if config.get("offer_id"): payload["offer_id"] = config["offer_id"]

        if not payload:
             return {"response": {"ok": False, "error_code": 400, "description": "Either product_id or offer_id is required"}}

        url = "https://api-seller.ozon.ru/v2/product/info"
        headers = {"Client-Id": str(client_id), "Api-Key": api_key, "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    return {"response": {"ok": True, "result": response.json().get("result", {})}}
                else:
                    return {"response": {"ok": False, "error_code": response.status_code, "description": response.text}}
        except Exception as e:
            return {"response": {"ok": False, "error_code": 500, "description": f"Internal error: {str(e)}"}}