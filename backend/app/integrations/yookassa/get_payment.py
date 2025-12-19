"""YooKassa Get Payment интеграция используя yookassa библиотеку."""
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


class YooKassaGetPaymentIntegration(BaseIntegration):
    """Интеграция для получения информации о платеже в YooKassa."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_get_payment",
            version="1.0.0",
            name="YooKassa Get Payment",
            description="Получение информации о платеже в YooKassa",
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
                        "description": "ID платежа для получения информации"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",  # Uses shop_id and secret_key
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о платеже",
                    "config": {
                        "payment_id": "{$session.payment_id$}"
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

        if not payment_id:
            await logger.error("payment_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Получаем информацию о платеже
            payment_info = Payment.find_one(payment_id)

            # Проверяем, что платеж существует
            if not payment_info:
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": f"Payment with ID {payment_id} not found"
                    }
                }

            # Извлекаем информацию о платеже
            payment_data = {
                "id": payment_info.id,
                "status": payment_info.status,
                "amount": payment_info.amount,
                "currency": payment_info.currency if hasattr(payment_info, 'currency') else None,
                "created_at": str(payment_info.created_at) if hasattr(payment_info, 'created_at') and payment_info.created_at else None,
                "captured_at": str(getattr(payment_info, 'captured_at', None)) if hasattr(payment_info, 'captured_at') and getattr(payment_info, 'captured_at', None) else None,
                "description": getattr(payment_info, 'description', None),
                "payment_method": {
                    "id": getattr(getattr(payment_info, 'payment_method', None), 'id', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) else None,
                    "type": getattr(getattr(payment_info, 'payment_method', None), 'type', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) else None,
                    "saved": getattr(getattr(payment_info, 'payment_method', None), 'saved', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) else None,
                    "card": {
                        "first6": getattr(getattr(getattr(payment_info, 'payment_method', None), 'card', None), 'first6', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None,
                        "last4": getattr(getattr(getattr(payment_info, 'payment_method', None), 'card', None), 'last4', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None,
                        "expiry_month": getattr(getattr(getattr(payment_info, 'payment_method', None), 'card', None), 'expiry_month', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None,
                        "expiry_year": getattr(getattr(getattr(payment_info, 'payment_method', None), 'card', None), 'expiry_year', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None,
                        "card_type": getattr(getattr(getattr(payment_info, 'payment_method', None), 'card', None), 'card_type', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None,
                        "issuer_country": getattr(getattr(getattr(payment_info, 'payment_method', None), 'card', None), 'issuer_country', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None,
                        "issuer_name": getattr(getattr(getattr(payment_info, 'payment_method', None), 'card', None), 'issuer_name', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None
                    } if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) and hasattr(getattr(payment_info, 'payment_method', None), 'card') else None,
                    "title": getattr(getattr(payment_info, 'payment_method', None), 'title', None) if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) else None
                } if hasattr(payment_info, 'payment_method') and getattr(payment_info, 'payment_method', None) else None,
                "paid": payment_info.paid if hasattr(payment_info, 'paid') else None,
                "refunded": getattr(payment_info, 'refunded', None),
                "refundable": getattr(payment_info, 'refundable', None),
                "test": getattr(payment_info, 'test', None),
                "receipt_registration": getattr(payment_info, 'receipt_registration', None),
                "metadata": getattr(payment_info, 'metadata', {}),
                "cancellation_details": getattr(payment_info, 'cancellation_details', None),
                "authorization_details": {
                    "rrn": getattr(getattr(payment_info, 'authorization_details', None), 'rrn', None) if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) else None,
                    "auth_code": getattr(getattr(payment_info, 'authorization_details', None), 'auth_code', None) if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) else None,
                    "three_d_secure": {
                        "applied": getattr(getattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure', None), 'applied', None) if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) and hasattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure') else None,
                        "sca_exemption": getattr(getattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure', None), 'sca_exemption', None) if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) and hasattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure') else None,
                        "acs_trans_id": getattr(getattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure', None), 'acs_trans_id', None) if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) and hasattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure') else None,
                        "trans_status": getattr(getattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure', None), 'trans_status', None) if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) and hasattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure') else None
                    } if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) and hasattr(getattr(payment_info, 'authorization_details', None), 'three_d_secure') else None
                } if hasattr(payment_info, 'authorization_details') and getattr(payment_info, 'authorization_details', None) else None
            }

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": payment_data
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

