"""Wildberries Get Product Info интеграция используя httpx для API запросов."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx для HTTP запросов
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class WildberriesGetProductInfoIntegration(BaseIntegration):
    """Интеграция для получения информации о продукте Wildberries через публичный API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="wildberries_get_product_info",
            version="1.0.0",
            name="Wildberries Get Product Info",
            description="Получение детальной информации о продукте с Wildberries по артикулу",
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#ff5722",
            config_schema={
                "type": "object",
                "required": ["product_id"],
                "properties": {
                    "product_id": {
                        "type": "string",
                        "title": "Product ID",
                        "description": "Артикул товара на Wildberries (числовое значение)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="none",
            library_name="httpx>=0.25.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о товаре",
                    "config": {
                        "product_id": "12345678"
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
        """
        Выполняет интеграцию используя httpx для запроса к Wildberries API.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }
        
        product_id = config.get("product_id")
        if not product_id:
            await logger.error("Product ID is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Product ID is required"
                }
            }
        
        try:
            # Wildberries API endpoint для получения информации о товаре
            url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={product_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get("data", {}).get("products"):
                    await logger.warning(f"No product found for ID: {product_id}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Product with ID {product_id} not found"
                        }
                    }
                
                product = data["data"]["products"][0]
                
                # Извлекаем основную информацию
                result = {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "brand": product.get("brand"),
                    "price": product.get("priceU", 0) // 100,  # Цена в рублях (копейки)
                    "sale_price": product.get("salePriceU", 0) // 100,
                    "rating": product.get("rating"),
                    "reviews_count": product.get("feedbacks"),
                    "supplier_id": product.get("supplierId"),
                    "category": product.get("subjName"),
                    "subcategory": product.get("subjRootName"),
                    "sizes": [
                        {
                            "name": size.get("name"),
                            "orig_name": size.get("origName"),
                            "rank": size.get("rank"),
                            "option_id": size.get("optionId"),
                            "stock": size.get("stocks", [])
                        } for size in product.get("sizes", [])
                    ],
                    "colors": [
                        {
                            "name": color.get("name"),
                            "id": color.get("id")
                        } for color in product.get("colors", [])
                    ],
                    "photos": [
                        f"https://images.wbstatic.net/c516x688/{photo}" 
                        for photo in product.get("pics", [])
                    ]
                }
                
                await logger.info(f"Successfully retrieved product info for ID: {product_id}")
                return {
                    "response": {
                        "ok": True,
                        "result": result
                    }
                }
                
        except httpx.HTTPStatusError as e:
            await logger.error(f"HTTP error while fetching product info: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"HTTP error: {e.response.text}"
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"Request error while fetching product info: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Request error: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while fetching product info: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }