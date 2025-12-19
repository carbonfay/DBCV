"""Wildberries Get Order интеграция используя прямые HTTP запросы через httpx."""
from typing import Dict, Any
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class WildberriesGetOrderIntegration(BaseIntegration):
    """Интеграция для получения информации о заказе из Wildberries используя прямые HTTP запросы."""
    
    # Wildberries API endpoints
    WILDBERRIES_API_BASE_URL = "https://api.wildberries.ru"
    WILDBERRIES_ORDERS_ENDPOINT = "/api/v1/supplier/orders"
    
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
                        "title": "Order ID",
                        "description": "ID заказа в Wildberries (можно использовать переменные: {$order.id$})"
                    },
                    "detailed": {
                        "type": "boolean",
                        "title": "Detailed Info",
                        "default": False,
                        "description": "Получить детальную информацию о заказе (товары, статусы и т.д.)"
                    }
                }
            },
            credentials_provider="wildberries",
            credentials_strategy="api_key",
            library_name=None,  # Не используем отдельную библиотеку, используем httpx
            examples=[
                {
                    "title": "Получить информацию о заказе",
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
        Выполняет интеграцию используя прямые HTTP запросы к Wildberries API.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        # Получаем order_id и параметры из config
        order_id = config.get("order_id")
        detailed = config.get("detailed", False)
        
        if not order_id:
            await logger.error("order_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "order_id is required parameter"
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
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        # Получаем API token - может быть под разными ключами
        api_token = payload.get("api_token") or payload.get("token") or payload.get("api_key")
        
        if not api_token:
            await logger.error(f"API token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API token not found in credentials"
                }
            }
        
        # ИСПОЛЬЗУЕМ HTTPX ДЛЯ ПРЯМЫХ HTTP ЗАПРОСОВ
        try:
            async with httpx.AsyncClient() as client:
                # Получаем заказ из Wildberries API
                # Wildberries API использует Authorization header с X-API-KEY
                headers = {
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json"
                }
                
                # Формируем URL для получения заказа
                # API может быть для конкретного заказа или нужно фильтровать из списка
                url = f"{self.WILDBERRIES_API_BASE_URL}{self.WILDBERRIES_ORDERS_ENDPOINT}"
                
                # Параметры для фильтрации
                params = {
                    "order_id": str(order_id)
                }
                
                # Делаем GET запрос к Wildberries API
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                # Обрабатываем различные коды ответа
                if response.status_code == 200:
                    data = response.json()
                    
                    # Wildberries API может вернуть список заказов, нужно найти нужный
                    orders = data.get("orders", [])
                    
                    if not orders:
                        await logger.warning(f"Order {order_id} not found in response")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 404,
                                "description": f"Order {order_id} not found"
                            }
                        }
                    
                    # Обычно API вернет один заказ, но на случай нескольких - возьмем первый
                    order = orders[0] if orders else None
                    
                    if not order:
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 404,
                                "description": f"Order {order_id} not found"
                            }
                        }
                    
                    # Формируем результат
                    if detailed:
                        # Детальная информация
                        result = {
                            "order_id": order.get("id"),
                            "number": order.get("number"),
                            "date": order.get("date"),
                            "status": order.get("status"),
                            "status_id": order.get("status_id"),
                            "status_description": order.get("status_description"),
                            "total": order.get("total"),
                            "convertedPrice": order.get("convertedPrice"),
                            "currency_code": order.get("currency_code"),
                            "items": order.get("items", []),
                            "address": order.get("address"),
                            "supplier_id": order.get("supplier_id"),
                            "client_id": order.get("client_id"),
                            "payment_type": order.get("payment_type"),
                            "comments": order.get("comments")
                        }
                    else:
                        # Краткая информация
                        result = {
                            "order_id": order.get("id"),
                            "number": order.get("number"),
                            "date": order.get("date"),
                            "status": order.get("status"),
                            "total": order.get("total"),
                            "currency_code": order.get("currency_code")
                        }
                    
                    # Возвращаем результат в формате системы
                    return {
                        "response": {
                            "ok": True,
                            "result": result
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
                
                elif response.status_code == 404:
                    await logger.warning(f"Order {order_id} not found (404)")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Order {order_id} not found"
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
                
                elif response.status_code >= 500:
                    await logger.error(f"Wildberries API server error ({response.status_code})")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": f"Wildberries API server error: {response.status_code}"
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
