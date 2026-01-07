"""Wildberries Get Orders интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Используем httpx для прямых HTTP запросов к Wildberries API
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class WildberriesGetOrdersIntegration(BaseIntegration):
    """Интеграция для получения заказов через Wildberries Supplier API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="wildberries_get_orders",
            version="1.0.0",
            name="Wildberries Get Orders",
            description="Получение списка заказов через Wildberries Supplier API (GET /api/v1/supplier/orders)",
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#9B1A30",
            config_schema={
                "type": "object",
                "properties": {
                    "dateFrom": {
                        "type": "string",
                        "title": "Date From",
                        "description": "Дата начала периода в формате ISO 8601 (например, 2024-01-01T00:00:00Z)",
                        "format": "date-time"
                    },
                    "dateTo": {
                        "type": "string",
                        "title": "Date To",
                        "description": "Дата окончания периода в формате ISO 8601 (например, 2024-01-31T23:59:59Z)",
                        "format": "date-time"
                    },
                    "status": {
                        "type": "integer",
                        "title": "Status",
                        "description": "Статус заказа (опционально)"
                    },
                    "take": {
                        "type": "integer",
                        "title": "Take",
                        "description": "Количество записей для получения (по умолчанию 100)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    },
                    "skip": {
                        "type": "integer",
                        "title": "Skip",
                        "description": "Количество записей для пропуска (по умолчанию 0)",
                        "default": 0,
                        "minimum": 0
                    }
                }
            },
            credentials_provider="wildberries",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить заказы за последний месяц",
                    "config": {
                        "dateFrom": "2024-01-01T00:00:00Z",
                        "dateTo": "2024-01-31T23:59:59Z",
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
        Выполняет интеграцию используя httpx для прямых HTTP запросов к Wildberries API.
        
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
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="wildberries",
            strategy="api_key"
        )
        
        if not creds:
            # Пробуем получить через get_single_for для обратной совместимости
            creds = await credentials_resolver.get_single_for(
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
                    "description": "Wildberries API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("statistics_token") or payload.get("supplier_token") or payload.get("token")
        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key not found in credentials"
                }
            }
        
        # Формируем параметры запроса
        params = {}
        if config.get("dateFrom"):
            params["dateFrom"] = config["dateFrom"]
        if config.get("dateTo"):
            params["dateTo"] = config["dateTo"]
        if config.get("status") is not None:
            params["status"] = config["status"]
        if config.get("take"):
            params["take"] = config["take"]
        if config.get("skip") is not None:
            params["skip"] = config["skip"]
        
        # Базовый URL для Wildberries Supplier API
        base_url = "https://suppliers-api.wildberries.ru"
        endpoint = "/api/v1/supplier/orders"
        url = f"{base_url}{endpoint}"
        
        # Заголовки для авторизации
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Выполняем HTTP запрос
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers
                )
                
                # Проверяем статус ответа
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "response": {
                            "ok": True,
                            "result": result
                        }
                    }
                else:
                    error_text = response.text
                    await logger.error(f"Wildberries API error: {response.status_code} - {error_text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": f"Wildberries API error: {error_text}"
                        }
                    }
        except httpx.TimeoutException as e:
            await logger.error(f"Wildberries API timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": f"Request timeout: {str(e)}"
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"Wildberries API request error: {e}")
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



