"""Wildberries Get Order интеграция для получения информации о конкретном заказе."""
from typing import Dict, Any, Optional
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class WildberriesGetOrderIntegration(BaseIntegration):
    """Интеграция для получения информации о конкретном заказе из Wildberries."""
    
    # Wildberries API endpoints
    WILDBERRIES_API_BASE_URL = "https://marketplace-api.wildberries.ru/"
    WILDBERRIES_ORDERS_ENDPOINT = "/api/v2/supplier/orders"
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="wildberries_get_order",
            version="1.0.0",
            name="Wildberries Get Order",
            description="Получить информацию о конкретном заказе из Wildberries",
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#9333ea",
            config_schema={
                "type": "object",
                "required": ["order_id"],
                "properties": {
                    "order_id": {
                        "type": "string",
                        "title": "ID заказа",
                        "description": "ID заказа в Wildberries (может содержать переменные вроде {$order.id$})"
                    },
                    "detailed": {
                        "type": "boolean",
                        "title": "Детальная информация",
                        "description": "Получить детальную информацию о заказе (товары, дополнительные поля)",
                        "default": False
                    }
                }
            },
            credentials_provider="wildberries",
            credentials_strategy="api_key",
            library_name=None,
            examples=[
                {
                    "title": "Получить информацию о заказе",
                    "config": {
                        "order_id": "12345678"
                    }
                },
                {
                    "title": "Получить детальную информацию о заказе",
                    "config": {
                        "order_id": "12345678",
                        "detailed": True
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
        Выполняет интеграцию для получения информации о конкретном заказе.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        # Получаем параметры из config
        order_id = config.get("order_id")
        detailed = config.get("detailed", False)
        
        if not order_id:
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "order_id is required"
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
                
                # Формируем параметры запроса для получения одного заказа
                params = {
                    "take": 1  # Получаем только один заказ
                }
                
                # Если нужна детальная информация
                if detailed:
                    params["detailed"] = "true"
                
                # Делаем GET запрос к Wildberries API
                url = f"{self.WILDBERRIES_API_BASE_URL}{self.WILDBERRIES_ORDERS_ENDPOINT}"
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                # Обработка ответа
                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("orders", [])
                    
                    # Ищем заказ с нужным ID
                    order = None
                    for o in orders:
                        if str(o.get("id")) == str(order_id) or str(o.get("number")) == str(order_id):
                            order = o
                            break
                    
                    if not order:
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 404,
                                "description": f"Order with id {order_id} not found"
                            }
                        }
                    
                    # Форматируем результат
                    result = self._format_order(order)
                    
                    return {
                        "response": {
                            "ok": True,
                            "result": result
                        }
                    }
                
                # Обработка ошибок
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
                        err = response.json()
                        error_msg = err.get("message") or err.get("error") or error_msg
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
    
    def _format_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует информацию о заказе для возвращения.
        
        Args:
            order: Данные заказа от API
            
        Returns:
            Отформатированная информация о заказе
        """
        formatted_order = {
            "id": order.get("id"),
            "number": order.get("number"),
            "date": order.get("date"),
            "status": order.get("status"),
            "status_id": order.get("status_id"),
            "status_description": order.get("status_description"),
            "total": order.get("total"),
            "currency_code": order.get("currency_code"),
            "items": self._format_items(order.get("items", [])) if order.get("items") else [],
            "items_count": len(order.get("items", [])) if order.get("items") else 0,
            "user": order.get("user"),
            "address": order.get("address"),
            "warehouse_id": order.get("warehouse_id")
        }
        
        return formatted_order
    
    def _format_items(self, items: list) -> list:
        """
        Форматирует список товаров в заказе.
        
        Args:
            items: Список товаров
            
        Returns:
            Отформатированный список товаров
        """
        formatted_items = []
        for item in items:
            formatted_item = {
                "id": item.get("id"),
                "vendorCode": item.get("vendorCode"),
                "nmId": item.get("nmId"),
                "skuId": item.get("skuId"),
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "price": item.get("price"),
                "total": item.get("total"),
                "status": item.get("status"),
                "warehouseId": item.get("warehouseId")
            }
            formatted_items.append(formatted_item)
        
        return formatted_items
