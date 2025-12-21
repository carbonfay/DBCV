"""Stripe Get Payment интеграция используя stripe библиотеку."""
from typing import Dict, Any
from uuid import UUID

from ...integrations.base import BaseIntegration, IntegrationMetadata
from ...auth.credentials_resolver import CredentialsResolver
from ...loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import stripe
    from stripe import StripeError
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None
    StripeError = Exception


class StripeGetPaymentIntegration(BaseIntegration):
    """Интеграция для получения информации о платеже в Stripe через stripe библиотеку."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_get_payment",
            version="1.0.0",
            name="Stripe Get Payment",
            description="Получение информации о существующем платеже в Stripe по ID",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635bff",
            config_schema={
                "type": "object",
                "required": ["payment_id"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа (PaymentIntent ID, например, 'pi_...')"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить платеж по ID",
                    "config": {
                        "payment_id": "pi_1234567890"
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
        Выполняет интеграцию используя библиотеку stripe.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not STRIPE_AVAILABLE:
            await logger.error("stripe library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "stripe library is not installed"
                }
            }
        
        # Получаем api_key из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="stripe",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Stripe credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Stripe api_key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key")
        if not api_key:
            await logger.error(f"api_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials"
                }
            }
        
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
            stripe.api_key = api_key
            
            # Получаем PaymentIntent по ID
            payment_intent = stripe.PaymentIntent.retrieve(str(payment_id))
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": payment_intent.id,
                        "status": payment_intent.status,
                        "amount": payment_intent.amount,
                        "currency": payment_intent.currency,
                        "description": payment_intent.description if hasattr(payment_intent, 'description') and payment_intent.description else None
                    }
                }
            }
        except StripeError as e:
            await logger.error(f"Stripe error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.http_status if hasattr(e, 'http_status') else 500,
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

