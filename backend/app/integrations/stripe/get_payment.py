"""Stripe Get Payment интеграция используя stripe библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None


class StripeGetPaymentIntegration(BaseIntegration):
    """Интеграция для получения информации о платеже в Stripe."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_get_payment",
            version="1.0.0",
            name="Stripe Get Payment",
            description="Получение информации о платеже в Stripe",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#6772E5",
            config_schema={
                "type": "object",
                "required": ["payment_intent_id"],
                "properties": {
                    "payment_intent_id": {
                        "type": "string",
                        "title": "Payment Intent ID",
                        "description": "ID платежного намерения для получения информации"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о платеже",
                    "config": {
                        "payment_intent_id": "{$session.payment_intent_id$}"
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

        secret_key = payload.get("secret_key") or payload.get("api_key") or payload.get("key")
        if not secret_key:
            await logger.error(f"Secret key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Secret key not found in credentials"
                }
            }

        # Устанавливаем API ключ
        stripe.api_key = secret_key

        # Получаем параметры из config
        payment_intent_id = config.get("payment_intent_id")

        if not payment_intent_id:
            await logger.error("payment_intent_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_intent_id is required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Получаем информацию о платеже
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Подготовим информацию о платеже для возврата
            payment_data = {
                "id": payment_intent.id,
                "object": payment_intent.object,
                "amount": payment_intent.amount,
                "amount_capturable": payment_intent.amount_capturable,
                "amount_received": payment_intent.amount_received,
                "application": payment_intent.application,
                "application_fee_amount": payment_intent.application_fee_amount,
                "automatic_payment_methods": getattr(payment_intent, 'automatic_payment_methods', None),
                "canceled_at": payment_intent.canceled_at,
                "cancellation_reason": payment_intent.cancellation_reason,
                "capture_method": payment_intent.capture_method,
                "client_secret": payment_intent.client_secret,
                "confirmation_method": payment_intent.confirmation_method,
                "created": payment_intent.created,
                "currency": payment_intent.currency,
                "customer": payment_intent.customer,
                "description": payment_intent.description,
                "invoice": payment_intent.invoice,
                "last_payment_error": getattr(payment_intent, 'last_payment_error', None),
                "livemode": payment_intent.livemode,
                "next_action": getattr(payment_intent, 'next_action', None),
                "on_behalf_of": payment_intent.on_behalf_of,
                "payment_method": payment_intent.payment_method,
                "payment_method_options": getattr(payment_intent, 'payment_method_options', {}),
                "payment_method_types": payment_intent.payment_method_types,
                "processing": getattr(payment_intent, 'processing', None),
                "receipt_email": payment_intent.receipt_email,
                "review": payment_intent.review,
                "setup_future_usage": payment_intent.setup_future_usage,
                "shipping": payment_intent.shipping,
                "source": payment_intent.source,
                "statement_descriptor": payment_intent.statement_descriptor,
                "statement_descriptor_suffix": payment_intent.statement_descriptor_suffix,
                "status": payment_intent.status,
                "transfer_data": payment_intent.transfer_data,
                "transfer_group": payment_intent.transfer_group
            }

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": payment_data
                }
            }
        except stripe.error.StripeError as e:
            await logger.error(f"Stripe API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.http_status or 500,
                    "description": f"Stripe API error: {str(e)}"
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

