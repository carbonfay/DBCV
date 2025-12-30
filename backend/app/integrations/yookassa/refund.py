"""YooKassa Refund интеграция используя yookassa библиотеку."""
import asyncio
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from yookassa import Configuration, Refund
    from yookassa.domain.exceptions import ApiError, UnauthorizedError
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Refund = None
    ApiError = Exception
    UnauthorizedError = Exception


class YooKassaRefundIntegration(BaseIntegration):
    """Интеграция для создания возврата платежа в YooKassa через yookassa SDK."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_refund",
            version="1.0.0",
            name="YooKassa Refund",
            description="Создание возврата платежа в YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#FFCC00",
            config_schema={
                "type": "object",
                "required": ["payment_id", "amount"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "Идентификатор платежа в YooKassa"
                    },
                    "amount": {
                        "type": "object",
                        "title": "Amount",
                        "description": "Сумма возврата",
                        "required": ["value", "currency"],
                        "properties": {
                            "value": {
                                "type": "string",
                                "title": "Value",
                                "description": "Сумма возврата (например, '100.00')"
                            },
                            "currency": {
                                "type": "string",
                                "title": "Currency",
                                "description": "Валюта (например, 'RUB')",
                                "default": "RUB"
                            }
                        }
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание возврата (опционально)"
                    },
                    "receipt": {
                        "type": "object",
                        "title": "Receipt",
                        "description": "Данные для чека при частичном возврате (опционально)"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Полный возврат платежа",
                    "config": {
                        "payment_id": "2c5b8d8e-0001-7000-8000-000000000000",
                        "amount": {
                            "value": "100.00",
                            "currency": "RUB"
                        }
                    }
                },
                {
                    "title": "Частичный возврат с описанием",
                    "config": {
                        "payment_id": "2c5b8d8e-0001-7000-8000-000000000000",
                        "amount": {
                            "value": "50.00",
                            "currency": "RUB"
                        },
                        "description": "Частичный возврат за отмененный товар"
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
        Выполняет интеграцию используя библиотеку yookassa.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed"
                }
            }
        
        # Получаем credentials из credentials_resolver
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="yookassa",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("YooKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials not found"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        shop_id = payload.get("shop_id") or payload.get("account_id")
        secret_key = payload.get("secret_key") or payload.get("api_key")
        
        if not shop_id or not secret_key:
            await logger.error(f"shop_id or secret_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id and secret_key are required in credentials"
                }
            }
        
        # Получаем параметры из config
        payment_id = config.get("payment_id")
        amount = config.get("amount")
        description = config.get("description")
        receipt = config.get("receipt")
        
        if not payment_id:
            await logger.error("payment_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required"
                }
            }
        
        if not amount:
            await logger.error("amount is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount is required"
                }
            }
        
        # Валидация amount
        if not isinstance(amount, dict):
            await logger.error("amount must be an object with 'value' and 'currency'")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount must be an object with 'value' and 'currency'"
                }
            }
        
        amount_value = amount.get("value")
        amount_currency = amount.get("currency", "RUB")
        
        if not amount_value:
            await logger.error("amount.value is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount.value is required"
                }
            }
        
        # Настраиваем конфигурацию YooKassa
        try:
            Configuration.account_id = str(shop_id)
            Configuration.secret_key = str(secret_key)
        except Exception as e:
            await logger.error(f"Failed to configure YooKassa: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Failed to configure YooKassa: {str(e)}"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        # Обертываем синхронный вызов в executor для избежания блокировки event loop
        try:
            # Подготавливаем данные для создания возврата
            refund_data = {
                "payment_id": str(payment_id),
                "amount": {
                    "value": str(amount_value),
                    "currency": str(amount_currency)
                }
            }
            
            if description:
                refund_data["description"] = str(description)
            
            if receipt:
                refund_data["receipt"] = receipt
            
            # Создаем возврат
            refund = await asyncio.to_thread(Refund.create, refund_data)
            
            # Преобразуем результат в словарь для возврата
            refund_dict = {
                "id": refund.id if hasattr(refund, 'id') else None,
                "status": refund.status if hasattr(refund, 'status') else None,
                "payment_id": refund.payment_id if hasattr(refund, 'payment_id') else None,
                "created_at": refund.created_at.isoformat() if hasattr(refund, 'created_at') and refund.created_at else None,
                "amount": {
                    "value": float(refund.amount.value) if hasattr(refund, 'amount') and hasattr(refund.amount, 'value') else None,
                    "currency": refund.amount.currency if hasattr(refund, 'amount') and hasattr(refund.amount, 'currency') else None
                } if hasattr(refund, 'amount') else None,
                "description": refund.description if hasattr(refund, 'description') else None,
                "receipt_registered": refund.receipt_registered if hasattr(refund, 'receipt_registered') else None
            }
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": refund_dict
                }
            }
        except UnauthorizedError as e:
            await logger.error(f"YooKassa unauthorized error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Unauthorized: {str(e)}"
                }
            }
        except ApiError as e:
            await logger.error(f"YooKassa API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.code if hasattr(e, 'code') else 400,
                    "description": str(e)
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

