"""YooKassa Refund интеграция используя yookassa библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import yookassa
    from yookassa import Refund, Payment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    yookassa = None
    Refund = None
    Payment = None


class YooKassaRefundIntegration(BaseIntegration):
    """Интеграция для возврата средств в YooKassa."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_refund",
            version="1.0.0",
            name="YooKassa Refund",
            description="Создание возврата средств в YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#F2B000",
            config_schema={
                "type": "object",
                "required": ["payment_id", "amount", "currency"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа для которого создается возврат"
                    },
                    "amount": {
                        "type": "number",
                        "title": "Amount",
                        "description": "Сумма возврата",
                        "minimum": 0.01
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "description": "Код валюты",
                        "default": "RUB",
                        "enum": ["RUB", "USD", "EUR", "GBP", "KZT"]
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание причины возврата"
                    },
                    "sources": {
                        "type": "array",
                        "title": "Sources",
                        "description": "Источники возврата (для распределения суммы возврата между разными источниками платежа)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "account_id": {
                                    "type": "string",
                                    "title": "Account ID",
                                    "description": "ID магазина-получателя средств"
                                },
                                "gateway_id": {
                                    "type": "string",
                                    "title": "Gateway ID",
                                    "description": "ID платежного шлюза"
                                },
                                "amount": {
                                    "type": "object",
                                    "title": "Amount",
                                    "properties": {
                                        "value": {
                                            "type": "string",
                                            "title": "Value",
                                            "description": "Сумма"
                                        },
                                        "currency": {
                                            "type": "string",
                                            "title": "Currency",
                                            "description": "Валюта"
                                        }
                                    }
                                },
                                "platform_fee_amount": {
                                    "type": "object",
                                    "title": "Platform Fee Amount",
                                    "properties": {
                                        "value": {
                                            "type": "string",
                                            "title": "Value",
                                            "description": "Комиссия платформы"
                                        },
                                        "currency": {
                                            "type": "string",
                                            "title": "Currency",
                                            "description": "Валюта"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",  # Uses shop_id and secret_key
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать возврат части суммы",
                    "config": {
                        "payment_id": "{$session.payment_id$}",
                        "amount": 500.00,
                        "currency": "RUB",
                        "description": "Возврат части оплаты по просьбе клиента"
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

        # Получаем учетные данные из credentials
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
                    "description": "YooKassa credentials not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        # YooKassa использует shop_id и secret_key
        shop_id = payload.get("shop_id")
        secret_key = payload.get("secret_key") or payload.get("api_key")
        
        if not shop_id or not secret_key:
            await logger.error(f"Shop ID or Secret key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Shop ID and Secret key are required for YooKassa"
                }
            }

        # Устанавливаем учетные данные
        yookassa.configuration.configure(shop_id, secret_key)

        # Получаем параметры из config
        payment_id = config.get("payment_id")
        amount = config.get("amount")
        currency = config.get("currency", "RUB") 
        description = config.get("description")
        sources = config.get("sources", [])

        if not payment_id or not amount:
            await logger.error("payment_id and amount are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id and amount are required"
                }
            }

        # Подготовим параметры для создания возврата
        refund_data = {
            "payment_id": payment_id,
            "amount": {
                "value": str(amount),
                "currency": currency
            }
        }

        if description:
            refund_data["description"] = str(description)
        
        if sources:
            refund_data["sources"] = sources

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем возврат
            refund = Refund.create(refund_data)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": refund.id,
                        "payment_id": refund.payment_id,
                        "status": refund.status,
                        "created_at": str(refund.created_at) if hasattr(refund, 'created_at') and refund.created_at else None,
                        "authorized_at": str(getattr(refund, 'authorized_at', None)) if hasattr(refund, 'authorized_at') and getattr(refund, 'authorized_at', None) else None,
                        "amount": refund.amount,
                        "receipt_registration": getattr(refund, 'receipt_registration', None),
                        "description": getattr(refund, 'description', None),
                        "sources": getattr(refund, 'sources', []),
                        "deal": getattr(refund, 'deal', None),
                        "refund_method": {
                            "type": getattr(refund.refund_method, 'type', None) if hasattr(refund, 'refund_method') and refund.refund_method else None
                        } if hasattr(refund, 'refund_method') and refund.refund_method else None
                    }
                }
            }
        except Exception as e:
            await logger.error(f"YooKassa API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

