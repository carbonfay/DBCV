"""Stripe Create Subscription интеграция используя stripe библиотеку."""
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


class StripeCreateSubscriptionIntegration(BaseIntegration):
    """Интеграция для создания подписки в Stripe."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_create_subscription",
            version="1.0.0",
            name="Stripe Create Subscription",
            description="Создание подписки в Stripe для рекуррентных платежей",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#6772E5",
            config_schema={
                "type": "object",
                "required": ["customer_id", "items"],
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "title": "Customer ID",
                        "description": "ID клиента в Stripe"
                    },
                    "items": {
                        "type": "array",
                        "title": "Subscription Items",
                        "description": "Элементы подписки (планы)",
                        "items": {
                            "type": "object",
                            "required": ["price"],
                            "properties": {
                                "price": {
                                    "type": "string",
                                    "title": "Price ID",
                                    "description": "ID тарифного плана"
                                },
                                "quantity": {
                                    "type": "integer",
                                    "title": "Quantity",
                                    "description": "Количество",
                                    "default": 1
                                }
                            }
                        }
                    },
                    "trial_period_days": {
                        "type": "integer",
                        "title": "Trial Period Days",
                        "description": "Период пробного периода в днях"
                    },
                    "trial_end": {
                        "type": "string",
                        "title": "Trial End",
                        "description": "Дата окончания пробного периода (в формате ISO 8601)"
                    },
                    "payment_behavior": {
                        "type": "string",
                        "title": "Payment Behavior",
                        "description": "Поведение при оплате",
                        "enum": ["allow_incomplete", "error_if_incomplete"],
                        "default": "allow_incomplete"
                    },
                    "expand": {
                        "type": "array",
                        "title": "Expand",
                        "description": "Объекты для расширения в ответе",
                        "items": {
                            "type": "string"
                        }
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать простую подписку",
                    "config": {
                        "customer_id": "{$session.stripe_customer_id$}",
                        "items": [
                            {
                                "price": "price_1234567890"
                            }
                        ]
                    }
                },
                {
                    "title": "Создать подписку с пробным периодом",
                    "config": {
                        "customer_id": "cus_1234567890",
                        "items": [
                            {
                                "price": "price_1234567890",
                                "quantity": 2
                            }
                        ],
                        "trial_period_days": 7
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
        customer_id = config.get("customer_id")
        items = config.get("items")
        trial_period_days = config.get("trial_period_days")
        trial_end = config.get("trial_end")
        payment_behavior = config.get("payment_behavior", "allow_incomplete")
        expand = config.get("expand", [])

        if not customer_id or not items or len(items) == 0:
            await logger.error("customer_id and items are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "customer_id and items are required"
                }
            }

        # Подготовим параметры для создания подписки
        subscription_params = {
            "customer": customer_id,
            "items": items,
            "payment_behavior": payment_behavior,
            "expand": expand
        }

        if trial_period_days:
            subscription_params["trial_period_days"] = int(trial_period_days)
        elif trial_end:
            import datetime
            trial_end_dt = datetime.datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
            subscription_params["trial_end"] = int(trial_end_dt.timestamp())

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем подписку
            subscription = stripe.Subscription.create(**subscription_params)

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
                        "trial_start": getattr(subscription, 'trial_start', None),
                        "trial_end": getattr(subscription, 'trial_end', None),
                        "created": subscription.created,
                        "cancel_at_period_end": subscription.cancel_at_period_end,
                        "canceled_at": subscription.canceled_at,
                        "cancel_at": subscription.cancel_at
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

