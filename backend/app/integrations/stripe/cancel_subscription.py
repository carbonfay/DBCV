"""Stripe Cancel Subscription интеграция используя stripe библиотеку."""
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


class StripeCancelSubscriptionIntegration(BaseIntegration):
    """Интеграция для отмены подписки в Stripe."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_cancel_subscription",
            version="1.0.0",
            name="Stripe Cancel Subscription",
            description="Отмена подписки в Stripe",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#6772E5",
            config_schema={
                "type": "object",
                "required": ["subscription_id"],
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "title": "Subscription ID",
                        "description": "ID подписки для отмены"
                    },
                    "invoice_now": {
                        "type": "boolean",
                        "title": "Invoice Now",
                        "description": "Выставить счет за оставшееся время",
                        "default": False
                    },
                    "prorate": {
                        "type": "boolean",
                        "title": "Prorate",
                        "description": "Начислить пропорциональную оплату",
                        "default": True
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Отменить подписку",
                    "config": {
                        "subscription_id": "{$session.subscription_id$}",
                        "invoice_now": True,
                        "prorate": True
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
        subscription_id = config.get("subscription_id")
        invoice_now = config.get("invoice_now", False)
        prorate = config.get("prorate", True)

        if not subscription_id:
            await logger.error("subscription_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "subscription_id is required"
                }
            }

        # Подготовим параметры для отмены подписки
        cancel_params = {
            "invoice_now": invoice_now,
            "prorate": prorate
        }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Отменяем подписку
            subscription = stripe.Subscription.delete(
                subscription_id,
                **cancel_params
            )

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": subscription.id,
                        "object": subscription.object,
                        "customer": subscription.customer,
                        "status": subscription.status,
                        "items": [
                            {
                                "id": item.id,
                                "price": {
                                    "id": item.price.id,
                                    "product": item.price.product,
                                    "unit_amount": item.price.unit_amount,
                                    "currency": item.price.currency
                                },
                                "quantity": item.quantity
                            } for item in subscription.items.data
                        ],
                        "current_period_start": subscription.current_period_start,
                        "current_period_end": subscription.current_period_end,
                        "ended_at": subscription.ended_at,
                        "canceled_at": subscription.canceled_at,
                        "cancel_at_period_end": subscription.cancel_at_period_end,
                        "cancel_at": subscription.cancel_at,
                        "created": subscription.created,
                        "trial_start": getattr(subscription, 'trial_start', None),
                        "trial_end": getattr(subscription, 'trial_end', None)
                    }
                }
            }
        except stripe.error.StripeError as e:
            await logger.error(f"Stripe API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.http_status or 400,
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

