"""Ozon Get Product List интеграция через HTTP запросы."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx для прямых запросов к Ozon API
try:
    import httpx
    HTTPX_AVAILABLE = True
    _HTTPX_HTTP_STATUS_ERROR = getattr(httpx, "HTTPStatusError", Exception)
    _HTTPX_TIMEOUT_ERROR = getattr(httpx, "TimeoutException", TimeoutError)
    _HTTPX_REQUEST_ERROR = getattr(httpx, "RequestError", Exception)
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None
    _HTTPX_HTTP_STATUS_ERROR = Exception
    _HTTPX_TIMEOUT_ERROR = TimeoutError
    _HTTPX_REQUEST_ERROR = Exception


class OzonGetProductListIntegration(BaseIntegration):
    """Интеграция для получения списка товаров Ozon через Seller API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="ozon_get_product_list",
            version="1.0.0",
            name="Ozon Get Product List",
            description="Получение списка товаров Ozon через POST /v2/product/list",
            category="ecommerce",
            icon_s3_key="icons/integrations/ozon.svg",
            color="#005BFF",
            config_schema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "object",
                        "title": "Filter",
                        "description": "Фильтр товаров Ozon",
                        "properties": {
                            "visibility": {
                                "type": "string",
                                "title": "Visibility",
                                "default": "ALL",
                                "description": "Видимость товаров (например: ALL, VISIBLE, INVISIBLE)"
                            },
                            "offer_id": {
                                "type": "array",
                                "title": "Offer IDs",
                                "items": {"type": "string"},
                                "description": "Список offer_id для фильтрации"
                            },
                            "product_id": {
                                "type": "array",
                                "title": "Product IDs",
                                "items": {"type": "integer"},
                                "description": "Список product_id для фильтрации"
                            }
                        }
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "default": 1000,
                        "description": "Количество товаров в ответе (1-1000)"
                    },
                    "last_id": {
                        "type": "string",
                        "title": "Last ID",
                        "description": "Идентификатор последнего товара для пагинации"
                    },
                    "visibility": {
                        "type": "string",
                        "title": "Visibility",
                        "description": "Упрощенное поле видимости (переопределяет filter.visibility)"
                    },
                    "offer_id": {
                        "type": "array",
                        "title": "Offer IDs",
                        "items": {"type": "string"},
                        "description": "Упрощенный список offer_id (переопределяет filter.offer_id)"
                    },
                    "product_id": {
                        "type": "array",
                        "title": "Product IDs",
                        "items": {"type": "integer"},
                        "description": "Упрощенный список product_id (переопределяет filter.product_id)"
                    }
                }
            },
            credentials_provider="ozon",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить список товаров",
                    "config": {
                        "limit": 100,
                        "visibility": "ALL"
                    }
                },
                {
                    "title": "Фильтр по offer_id",
                    "config": {
                        "limit": 50,
                        "offer_id": ["SKU-001", "SKU-002"]
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
        Выполняет интеграцию через Ozon Seller API.

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

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="ozon",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Ozon credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Ozon credentials not found"
                }
            }

        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        client_id = payload.get("client_id") or payload.get("clientId")
        api_key = payload.get("api_key") or payload.get("apiKey")

        if not client_id or not api_key:
            await logger.error(
                "client_id or api_key not found in credentials. "
                f"Available keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "client_id and api_key are required in Ozon credentials"
                }
            }

        limit = config.get("limit", 1000)
        if limit is None:
            limit = 1000

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            await logger.error("limit must be an integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "limit must be an integer"
                }
            }

        if limit <= 0 or limit > 1000:
            await logger.error("limit must be between 1 and 1000")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "limit must be between 1 and 1000"
                }
            }

        last_id = config.get("last_id")
        filter_config = config.get("filter") if isinstance(config.get("filter"), dict) else {}

        visibility = config.get("visibility") or filter_config.get("visibility")
        offer_id = config.get("offer_id") or filter_config.get("offer_id")
        product_id = config.get("product_id") or filter_config.get("product_id")

        def _normalize_list(value):
            if value is None:
                return None
            if isinstance(value, list):
                return value
            return [value]

        filter_payload = dict(filter_config)
        if visibility:
            filter_payload["visibility"] = visibility
        if offer_id is not None:
            filter_payload["offer_id"] = _normalize_list(offer_id)
        if product_id is not None:
            filter_payload["product_id"] = _normalize_list(product_id)

        request_data: Dict[str, Any] = {
            "filter": filter_payload,
            "limit": limit
        }
        if last_id:
            request_data["last_id"] = str(last_id)

        url = "https://api-seller.ozon.ru/v2/product/list"
        headers = {
            "Client-Id": str(client_id),
            "Api-Key": str(api_key),
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=request_data,
                    headers=headers,
                    timeout=30.0
                )

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    await logger.error("Invalid JSON response from Ozon API")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": "Invalid JSON response from Ozon API"
                        }
                    }

                await logger.info("Successfully retrieved Ozon product list")
                return {
                    "response": {
                        "ok": True,
                        "result": data
                    }
                }

            error_text = response.text
            try:
                error_data = response.json()
                error_message = error_data.get("message") or error_data.get("error") or error_text
            except ValueError:
                error_message = error_text

            await logger.error(f"Ozon API error: {response.status_code} - {error_message}")
            return {
                "response": {
                    "ok": False,
                    "error_code": response.status_code,
                    "description": error_message
                }
            }

        except _HTTPX_TIMEOUT_ERROR:
            await logger.error("Ozon API request timeout")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": "Ozon API request timeout"
                }
            }
        except _HTTPX_REQUEST_ERROR as e:
            await logger.error(f"Ozon API request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Ozon API request error: {str(e)}"
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
