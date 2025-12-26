from typing import Dict, Any
from uuid import UUID
import asyncio
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Попытка импортировать библиотеку Wildberries напрямую. Если её нет — помечаем как недоступную.
try:
    import wildberries_api  # type: ignore
    from wildberries_api.exceptions import WildberriesAPIError, AuthenticationError  # type: ignore
    WILDBERRIES_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    wildberries_api = None  # type: ignore
    WildberriesAPIError = Exception  # type: ignore
    AuthenticationError = Exception  # type: ignore
    WILDBERRIES_AVAILABLE = False




class WildberriesUpdateStockIntegration(BaseIntegration):
    """Интеграция для обновления остатков на Wildberries.

    Использует библиотеку `wildberries_api` напрямую (если установлена).
    """

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="wildberries_update_stock",
            version="1.0.0",
            name="Wildberries Update Stock",
            description="Обновляет количество товара (stock) по артикулу (sku) на Wildberries",
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#ff6600",
            config_schema={
                "type": "object",
                "required": ["sku", "stock"],
                "properties": {
                    "sku": {
                        "type": "string",
                        "title": "SKU",
                        "description": "Артикул товара на Wildberries"
                    },
                    "stock": {
                        "type": "integer",
                        "minimum": 0,
                        "title": "Stock",
                        "description": "Количество на складе"
                    },
                    "warehouse_id": {
                        "type": "string",
                        "title": "Warehouse ID",  # ← Оставляем как есть (возможна специфика API)
                        "description": "ID склада (опционально)"
                    }
                }
            },
            credentials_provider="wildberries",
            credentials_strategy="api_key",
            library_name=("wildberries-api>=1.2.0" if WILDBERRIES_AVAILABLE else None),
            examples=[
                {
                    "title": "Обновление остатка",
                    "config": {"sku": "WB12345", "stock": 50}
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """
        Выполняет обновление остатков через библиотеку Wildberries.

        Параметры:
            config: Словарь с параметрами интеграции (sku, stock, warehouse_id).
            credentials_resolver: Объект для получения учётных данных.
            bot_id: Уникальный идентификатор бота.
            logger: Объект логгера для записи событий.

        Возвращает:
            Словарь с результатом в формате платформы:
            {
                "response": {
                    "ok": bool,
                    "error_code": int | None,
                    "description": str | None,
                    "error": str | None,
                    "result": Any | None
                }
            }
        """
        try:
            # Логирование начала выполнения интеграции
            await logger.info(
                f"Starting WildberriesUpdateStockIntegration execution. "
                f"Bot ID: {bot_id}, Config: {json.dumps(config)}"
            )

            if not WILDBERRIES_AVAILABLE:
                await logger.error("wildberries_api library is not available")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "wildberries_api library is not installed",
                        "error": None,
                        "result": None
                    }
                }

            # Получаем credentials
            await logger.debug(f"Fetching Wildberries credentials for bot ID: {bot_id}")
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id, provider="wildberries", strategy="api_key"
            )

            if not creds:
                await logger.error(f"Wildberries credentials not found for bot ID: {bot_id}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "Wildberries api_key not found in credentials",
                        "error": None,
                        "result": None
                    }
                }

            # Проверяем тип creds
            if not isinstance(creds, dict):
                await logger.error(
                    f"Invalid credentials format: expected dict, got {type(creds)}. Bot ID: {bot_id}"
                )
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "Invalid credentials format",
                        "error": f"Expected dict, got {type(creds)}",
                        "result": None
                    }
                }

            # Credentials могут храниться в поле payload
            payload = creds.get("payload", {})
            api_key = payload.get("api_key") or payload.get("token")

            if not api_key:
                await logger.error(
                    f"api_key not found in Wildberries credentials for bot ID: {bot_id}. "
                    f"Payload: {json.dumps(payload)}"
                )
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "api_key not found in credentials",
                        "error": None,
                        "result": None
                    }
                }

            await logger.debug(f"Successfully retrieved API key: {api_key[:5]}... (truncated)")

            # Валидация входных параметров
            sku = config.get("sku")
            stock = config.get("stock")
            warehouse_id = config.get("warehouse_id")

            if not sku or stock is None:
                error_msg = "sku and stock are required for WildberriesUpdateStockIntegration"
                await logger.error(f"{error_msg}. Provided config: {json.dumps(config)}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": error_msg,
                        "error": None,
                        "result": None
                    }
                }

            if not isinstance(stock, int) or stock < 0:
                error_msg = "stock must be a non-negative integer"
                await logger.error(f"{error_msg}. Value: {stock}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": error_msg,
                        "error": None,
                        "result": None
                    }
                }

            await logger.info(
                f"Validated input parameters. SKU: {sku}, Stock: {stock}, Warehouse ID: {warehouse_id}"
            )

                        # Инициализируем клиент
            await logger.debug("Initializing Wildberries API client")
            client = wildberries_api.Client(api_key=api_key)

            # Вызов API с таймаутом
            try:
                await logger.debug(
                    f"Calling update_stock with sku={sku}, stock={stock}, warehouse_id={warehouse_id}"
                )
                # Проверяем, нужен ли warehouse_id
                if warehouse_id:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.update_stock,
                            sku=sku,
                            stock=stock,
                            warehouse_id=warehouse_id
                        ),
                        timeout=30.0
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.update_stock,
                            sku=sku,
                            stock=stock
                        ),
                        timeout=30.0
                    )
            except asyncio.TimeoutError:
                await logger.error("API request timed out after 30 seconds")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 504,
                        "description": "API request timed out",
                        "error": "Request to Wildberries API exceeded 30 seconds",
                        "result": None
                    }
                }
            except TypeError as te:
                await logger.warning(
                    f"update_stock failed with TypeError: {te}. Retrying without warehouse_id for sku={sku}"
                )
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(client.update_stock, sku=sku, stock=stock),
                        timeout=30.0
                    )
                except Exception as retry_error:
                    await logger.error(f"Retry failed: {retry_error}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": "Failed to update stock",
                            "error": str(retry_error),
                            "result": None
                        }
                    }

            # Проверяем результат API
            if result is None:
                await logger.error("API returned None (empty response)")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 502,
                        "description": "Empty response from Wildberries API",
                        "error": "API returned None",
                        "result": None
                    }
                }

            await logger.info(
                f"Stock update successful. SKU: {sku}, New Stock: {stock}, Result: {json.dumps(result)}"
            )
            return {
                "response": {
                    "ok": True,
                    "error_code": None,
                    "description": None,
                    "error": None,
                    "result": result
                }
            }

        except AuthenticationError as e:
            error_msg = f"Authentication failed: {e}"
            await logger.error(error_msg)
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Authentication failed",
                    "error": error_msg,
                    "result": None
                }
            }

        except WildberriesAPIError as e:
            error_msg = f"Wildberries API error: {e}"
            await logger.error(error_msg)
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, "status_code", 500),  # Если у исключения есть статус
                    "description": "Wildberries API returned an error",
                    "error": error_msg,
                    "result": None
                }
            }

        except asyncio.CancelledError:
            # Ловим отмену задачи (например, при shutdown)
            await logger.warning("WildberriesUpdateStockIntegration execution was cancelled")
            raise  # Передаём дальше, т. к. это управляемое прерывание

        except Exception as e:
            error_msg = f"Unexpected error in WildberriesUpdateStockIntegration: {e}"
            await logger.critical(error_msg, exc_info=True)  # Логируем стектрейс
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "Internal server error",
                    "error": error_msg,
                    "result": None
                }
            }