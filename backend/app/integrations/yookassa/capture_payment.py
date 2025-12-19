"""YooKassa Capture Payment интеграция используя yookassa библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import yookassa
    from yookassa import Payment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    yookassa = None
    Payment = None


class YooKassaCapturePaymentIntegration(BaseIntegration):
    """Интеграция для подтверждения (capture) платежей в YooKassa."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_capture_payment",
            version="1.0.0",
            name="YooKassa Capture Payment",
            description="Подтверждение (capture) платежа в YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#F2B000",
            config_schema={
                "type": "object",
                "required": ["payment_id"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа для подтверждения"
                    },
                    "amount": {
                        "type": "number",
                        "title": "Amount",
                        "description": "Сумма для подтверждения (если меньше исходной, будет частичное подтверждение)",
                        "minimum": 0.01
                    },
                    "transferred_amount": {
                        "type": "number",
                        "title": "Transferred Amount",
                        "description": "Сумма, которая будет перечислена магазину",
                        "minimum": 0.01
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",  # Uses shop_id and secret_key
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Подтвердить платеж полностью",
                    "config": {
                        "payment_id": "{$session.payment_id$}"
                    }
                },
                {
                    "title": "Частичное подтверждение платежа",
                    "config": {
                        "payment_id": "1234567890",
                        "amount": 500.00
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
        transferred_amount = config.get("transferred_amount")

        if not payment_id:
            await logger.error("payment_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required"
                }
            }

        # Подготовим параметры для подтверждения платежа
        capture_data = {}

        if amount:
            capture_data["amount"] = {
                "value": str(amount),
                "currency": "RUB"
            }

        if transferred_amount:
            capture_data["transferred_amount"] = {
                "value": str(transferred_amount),
                "currency": "RUB"
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Подтверждаем платеж
            payment = Payment.capture(payment_id, capture_data)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": payment.id,
                        "status": payment.status,
                        "amount": payment.amount,
                        "description": payment.description,
                        "receipt_registration": getattr(payment, 'receipt_registration', None),
                        "created_at": str(payment.created_at) if hasattr(payment, 'created_at') and payment.created_at else None,
                        "expires_at": str(getattr(payment, 'expires_at', None)) if hasattr(payment, 'expires_at') and getattr(payment, 'expires_at', None) else None,
                        "payment_method": {
                            "type": getattr(payment.payment_method, 'type', None) if hasattr(payment, 'payment_method') and payment.payment_method else None
                        } if hasattr(payment, 'payment_method') and payment.payment_method else None,
                        "confirmation": {
                            "type": getattr(payment.confirmation, 'type', None) if hasattr(payment.confirmation, 'confirmation') and payment.confirmation else None,
                            "confirmation_url": getattr(payment.confirmation, 'confirmation_url', None) if hasattr(payment.confirmation, 'confirmation') and payment.confirmation else None
                        } if hasattr(payment, 'confirmation') and payment.confirmation else None,
                        "paid": payment.paid,
                        "refundable": payment.refundable,
                        "merchant_customer_id": getattr(payment, 'merchant_customer_id', None)
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

