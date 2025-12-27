"""Ozon Get Product Info интеграция используя httpx для прямых запросов к Ozon API."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx для прямых запросов к API
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class OzonGetProductInfoIntegration(BaseIntegration):
    """Интеграция для получения информации о товаре в Ozon через прямые HTTP запросы."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="ozon_get_product_info",
            version="1.0.0",
            name="Ozon Get Product Info",
            description="Получение детальной информации о товаре в Ozon по артикулу или SKU",
            category="ecommerce",
            icon_s3_key="icons/integrations/ozon.svg",
            color="#005bff",
            config_schema={
                "type": "object",
                "required": ["product_id"],
                "properties": {
                    "product_id": {
                        "type": "string",
                        "title": "Product ID",
                        "description": "Артикул товара (SKU) или ID товара в Ozon"
                    },
                    "language": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык ответа (ru, en, etc.)",
                        "default": "ru",
                        "enum": ["ru", "en"]
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получение информации о товаре",
                    "config": {
                        "product_id": "123456789",
                        "language": "ru"
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
        Выполняет интеграцию используя прямые HTTP запросы к Ozon API.
        
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
        
        # Получаем API ключ из credentials
        await logger.info(f"Looking for credentials for bot_id: {bot_id}")
        
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Ozon credentials not found for provider 'other', strategy 'api_key'")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Ozon API key not found in credentials"
                }
            }
        
        # Debug: логируем что получили
        await logger.info(f"Found credentials: {creds}")
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        # Debug: логируем payload
        await logger.info(f"Payload content: {payload}")
        await logger.info(f"Available keys in payload: {list(payload.keys())}")
        
        api_key = payload.get("api_key") or payload.get("token")
        client_id = payload.get("client_id")
        
        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key not found in credentials"
                }
            }
        
        if not client_id:
            await logger.error(f"Client ID not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Client ID not found in credentials"
                }
            }
        
        # Получаем параметры из config
        product_id = config.get("product_id")
        language = config.get("language", "ru")
        
        if not product_id:
            await logger.error("product_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "product_id is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ HTTP ЗАПРОСЫ НАПРЯМУЮ
        try:
            # Ozon Product Info API endpoint
            url = "https://api-seller.ozon.ru/v2/products/info"
            
            headers = {
                "Client-Id": str(client_id),
                "Api-Key": str(api_key),
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Для v2 API используем правильную структуру запроса
            data = {
                "product_id": [int(product_id)],  # Ozon ожидает массив чисел
                "language": language
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Ozon возвращает массив товаров
                    products = result.get("result", {}).get("items", [])
                    if not products:
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 404,
                                "description": "Product not found"
                            }
                        }
                    
                    product = products[0]  # Берем первый товар
                    
                    # Возвращаем результат в формате системы
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "product_id": product.get("product_id"),
                                "title": product.get("title"),
                                "description": product.get("description"),
                                "price": product.get("price"),
                                "currency": product.get("currency"),
                                "brand": product.get("brand"),
                                "category": product.get("category"),
                                "images": product.get("images", []),
                                "availability": product.get("availability"),
                                "rating": product.get("rating"),
                                "reviews_count": product.get("reviews_count"),
                                "url": product.get("url")
                            }
                        }
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    await logger.error(f"Ozon API error: {response.status_code} - {error_data}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": error_data.get("message", f"HTTP {response.status_code}")
                        }
                    }
                    
        except httpx.HTTPStatusError as e:
            await logger.error(f"Ozon HTTP error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": f"HTTP error: {e.response.status_code}"
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"Ozon request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Request error: {str(e)}"
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
