"""Wildberries Get Orders интеграция используя прямые HTTP запросы через httpx."""
from typing import Dict, Any, List, Optional
from uuid import UUID
import httpx
from datetime import datetime

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class WildberriesGetOrdersIntegration(BaseIntegration):
    """Интеграция для получения списка заказов из Wildberries с пагинацией и фильтрацией."""
    
    # Wildberries API endpoints
    WILDBERRIES_API_BASE_URL = "https://marketplace-api.wildberries.ru/"
    WILDBERRIES_ORDERS_ENDPOINT = "/api/v2/supplier/orders"
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="wildberries_get_orders",
            version="1.0.0",
            name="Wildberries Get Orders",
            description="Получить список заказов из Wildberries с пагинацией и фильтрацией",
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#9333ea",
            config_schema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "title": "Статус заказа",
                        "description": "Фильтр по статусу заказа (например, 'new', 'confirm', 'cancel' и т.д.)",
                        "default": ""
                    },
                    "date_start": {
                        "type": "string",
                        "format": "date",
                        "title": "Дата начала",
                        "description": "Начальная дата для фильтрации заказов (формат: ГГГГ-ММ-ДД)"
                    },
                    "date_end": {
                        "type": "string",
                        "format": "date",
                        "title": "Дата окончания",
                        "description": "Конечная дата для фильтрации заказов (формат: ГГГГ-ММ-ДД)"
                    },
                    "skip": {
                        "type": "integer",
                        "title": "Пропустить первых N",
                        "description": "Количество записей, которые нужно пропустить (для пагинации)",
                        "minimum": 0,
                        "default": 0
                    },
                    "take": {
                        "type": "integer",
                        "title": "Количество записей",
                        "description": "Максимальное количество возвращаемых записей (1-1000)",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 50
                    }
                }
            },
            credentials_provider="wildberries",
            credentials_strategy="api_key",
            library_name=None,
            examples=[
                {
                    "title": "Получить последние 50 заказов",
                    "config": {
                        "skip": 0,
                        "take": 50
                    }
                },
                {
                    "title": "Получить заказы за определенный период",
                    "config": {
                        "date_start": "2024-01-01",
                        "date_end": "2024-12-31",
                        "status": "delivered",
                        "skip": 0,
                        "take": 100
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
        Выполняет интеграцию для получения списка заказов.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        # Получаем параметры из config
        status = config.get("status", "")
        date_start = config.get("date_start")
        date_end = config.get("date_end")
        skip = max(0, int(config.get("skip", 0)))
        take = max(1, min(1000, int(config.get("take", 50))))
        
        # Валидация дат
        if date_start and date_end:
            try:
                start_date = datetime.strptime(date_start, "%Y-%m-%d")
                end_date = datetime.strptime(date_end, "%Y-%m-%d")
                if start_date > end_date:
                    date_start, date_end = date_end, date_start
            except ValueError:
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "Invalid date format. Use YYYY-MM-DD"
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
                
                # Формируем параметры запроса
                params = {
                    "skip": skip,
                    "take": take
                }
                
                # Добавляем фильтры, если они указаны
                if status:
                    params["status"] = status
                if date_start:
                    params["date_start"] = date_start
                if date_end:
                    params["date_end"] = date_end
                
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
                    total = data.get("total", len(orders))
                    
                    # Форматируем результат
                    result = {
                        "count": len(orders),
                        "total": total,
                        "skip": skip,
                        "take": take,
                        "orders": self._format_orders(orders)
                    }
                    
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
    
    def _format_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Форматирует список заказов для возвращения.
        
        Args:
            orders: Список заказов от API
            
        Returns:
            Отформатированный список заказов
        """
        formatted = []
        for order in orders:
            formatted_order = {
                "id": order.get("id"),
                "number": order.get("number"),
                "date": order.get("date"),
                "status": order.get("status"),
                "status_id": order.get("status_id"),
                "status_description": order.get("status_description"),
                "total": order.get("total"),
                "currency_code": order.get("currency_code"),
                "items_count": len(order.get("items", [])) if order.get("items") else 0
            }
            formatted.append(formatted_order)
        
        return formatted