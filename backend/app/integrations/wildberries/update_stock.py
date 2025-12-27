"""Wildberries Update Stock интеграция используя прямые HTTP запросы через httpx."""
from typing import Dict, Any, List
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class WildberriesUpdateStockIntegration(BaseIntegration):
    """Интеграция для обновления остатков товаров в Wildberries."""
    
    # Wildberries API endpoints
    WILDBERRIES_API_BASE_URL = "https://marketplace-api.wildberries.ru"
    WILDBERRIES_STOCKS_ENDPOINT = "/api/v2/supplier/stocks"
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="wildberries_update_stock",
            version="1.0.0",
            name="Wildberries Update Stock",
            description="Обновление остатков товаров в Wildberries",
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#9333ea",
            config_schema={
                "type": "object",
                "required": ["stocks"],
                "properties": {
                    "stocks": {
                        "type": "array",
                        "title": "Список остатков",
                        "items": {
                            "type": "object",
                            "required": ["barcode", "stock"],
                            "properties": {
                                "barcode": {
                                    "type": "string",
                                    "title": "Баркод товара"
                                },
                                "stock": {
                                    "type": "integer",
                                    "title": "Количество",
                                    "minimum": 0
                                },
                                "warehouse_id": {
                                    "type": "integer",
                                    "title": "ID склада (опционально)"
                                }
                            }
                        }
                    }
                }
            },
            credentials_provider="wildberries",
            credentials_strategy="api_key",
            library_name=None,
            examples=[
                {
                    "title": "Обновить остатки для одного товара",
                    "config": {
                        "stocks": [
                            {
                                "barcode": "1234567890123",
                                "stock": 10,
                                "warehouse_id": 123
                            }
                        ]
                    }
                },
                {
                    "title": "Обновить остатки для нескольких товаров",
                    "config": {
                        "stocks": [
                            {
                                "barcode": "1234567890123",
                                "stock": 5
                            },
                            {
                                "barcode": "9876543210987",
                                "stock": 15,
                                "warehouse_id": 123
                            }
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
        """
        Выполняет обновление остатков товаров в Wildberries.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        # Получаем список остатков из конфига
        stocks = config.get("stocks", [])
        
        if not stocks:
            await logger.error("No stocks provided in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "No stocks provided in config"
                }
            }
        
        # Валидация входных данных
        for i, stock in enumerate(stocks):
            if "barcode" not in stock or "stock" not in stock:
                await logger.error(f"Invalid stock data at index {i}: {stock}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"Invalid stock data at index {i}: missing required fields"
                    }
                }
            
            # Проверяем, что stock - неотрицательное число
            try:
                stock["stock"] = int(stock["stock"])
                if stock["stock"] < 0:
                    raise ValueError("Stock cannot be negative")
            except (ValueError, TypeError):
                await logger.error(f"Invalid stock value at index {i}: {stock.get('stock')}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"Invalid stock value at index {i}: must be a non-negative integer"
                    }
                }
        
        # Получаем API token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="wildberries",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Wildberries credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Wildberries API token not found in credentials"
                }
            }
        
        # Получаем API token
        payload = creds.get("payload", {}) or creds
        api_key = payload.get("api_key") or payload.get("api_token") or payload.get("token")

        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key not found in credentials"
                }
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # Настройка заголовков
                headers = {
                    "X-API-KEY": api_key,
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Формируем URL для обновления остатков
                url = f"{self.WILDBERRIES_API_BASE_URL}{self.WILDBERRIES_STOCKS_ENDPOINT}"
                
                # Отправляем PUT запрос
                response = await client.put(
                    url,
                    headers=headers,
                    json=stocks,
                    timeout=30.0
                )
                
                # Обработка ответа
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "updated": len(stocks),
                                "details": data
                            }
                        }
                    }
                
                # Обработка ошибок
                elif response.status_code == 400:
                    error_msg = "Bad request"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message") or error_data.get("error") or error_msg
                    except Exception:
                        pass
                    
                    await logger.error(f"Wildberries API bad request (400): {error_msg}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"Bad request: {error_msg}"
                        }
                    }
                
                elif response.status_code == 401:
                    await logger.error("Wildberries API authentication failed (401)")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 401,
                            "description": "Wildberries API authentication failed"
                        }
                    }
                
                elif response.status_code == 403:
                    error_msg = "Forbidden: Invalid API key or insufficient permissions"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message") or error_data.get("error") or error_msg
                    except Exception:
                        pass
                    
                    await logger.error(f"Wildberries API forbidden (403): {error_msg}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 403,
                            "description": error_msg
                        }
                    }
                
                elif response.status_code == 429:
                    await logger.error("Rate limit exceeded (429)")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 429,
                            "description": "Rate limit exceeded"
                        }
                    }
                
                else:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message") or error_data.get("error") or error_msg
                    except Exception:
                        pass
                    
                    await logger.error(f"Wildberries API error: {response.status_code} - {error_msg}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": f"Wildberries API error: {error_msg}"
                        }
                    }
        
        except httpx.TimeoutException:
            await logger.error("Wildberries API request timeout")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": "Wildberries API request timeout"
                }
            }
        
        except httpx.RequestError as e:
            await logger.error(f"Wildberries API request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Wildberries API request error: {str(e)}"
                }
            }
        
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }