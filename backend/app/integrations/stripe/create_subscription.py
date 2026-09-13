"""Stripe Create Subscription интеграция используя официальную библиотеку stripe."""
import asyncio
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import stripe
    from stripe import StripeError
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None
    StripeError = Exception


class StripeCreateSubscriptionIntegration(BaseIntegration):
    """Интеграция для создания подписки (Subscription) клиента в Stripe через официальный SDK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_create_subscription",
            version="1.0.0",
            name="Stripe Create Subscription",
            description="Создание регулярной подписки клиента на один или несколько тарифов (Price) в Stripe",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635BFF",
            config_schema={
                "type": "object",
                "required": ["customer_id", "items"],
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "title": "Customer ID",
                        "description": "ID клиента в Stripe, на которого оформляется подписка (например, cus_ABC123)"
                    },
                    "items": {
                        "type": "array",
                        "title": "Items",
                        "description": "Список позиций подписки: ID тарифа (Price) и количество",
                        "items": {
                            "type": "object",
                            "properties": {
                                "price": {
                                    "type": "string",
                                    "title": "Price ID"
                                },
                                "quantity": {
                                    "type": "integer",
                                    "title": "Quantity"
                                }
                            }
                        }
                    },
                    "trial_period_days": {
                        "type": "integer",
                        "title": "Trial Period Days",
                        "description": "Количество дней бесплатного пробного периода"
                    },
                    "payment_behavior": {
                        "type": "string",
                        "title": "Payment Behavior",
                        "description": "Поведение при создании подписки, если платёж не проходит сразу",
                        "enum": ["default_incomplete", "error_if_incomplete", "allow_incomplete", "pending_if_incomplete"],
                        "default": "default_incomplete"
                    },
                    "coupon": {
                        "type": "string",
                        "title": "Coupon",
                        "description": "ID купона/промокода для применения скидки"
                    },
                    "default_payment_method": {
                        "type": "string",
                        "title": "Default Payment Method",
                        "description": "ID метода оплаты по умолчанию для подписки"
                    },
                    "automatic_tax": {
                        "type": "boolean",
                        "title": "Automatic Tax",
                        "description": "Включить автоматический расчёт налогов Stripe Tax",
                        "default": False
                    },
                    "metadata": {
                        "type": "object",
                        "title": "Metadata",
                        "description": "Произвольные метаданные подписки в формате ключ-значение"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Подписка на один тариф с триалом",
                    "config": {
                        "customer_id": "cus_ABC123",
                        "items": [{"price": "price_1N...", "quantity": 1}],
                        "trial_period_days": 7
                    }
                },
                {
                    "title": "Подписка на несколько тарифов с купоном и автоналогами",
                    "config": {
                        "customer_id": "cus_ABC123",
                        "items": [
                            {"price": "price_base", "quantity": 1},
                            {"price": "price_addon_seats", "quantity": 3}
                        ],
                        "coupon": "WELCOME10",
                        "automatic_tax": True
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
        Создаёт подписку клиента в Stripe используя stripe.Subscription.create().

        Args:
            config: Параметры интеграции (customer_id, items и опциональные поля подписки)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер для записи логов

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

        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        api_key = payload.get("api_key") or payload.get("secret_key")
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
        customer_id = config.get("customer_id")
        raw_items = config.get("items")

        if not customer_id:
            await logger.error("customer_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "customer_id is required"
                }
            }

        if not raw_items or not isinstance(raw_items, list):
            await logger.error("items must be a non-empty list of {price, quantity}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items must be a non-empty list of {price, quantity}"
                }
            }

        subscription_items = []
        for item in raw_items:
            price_id = item.get("price") if isinstance(item, dict) else None
            if not price_id:
                continue
            subscription_item = {"price": price_id}
            quantity = item.get("quantity")
            if quantity is not None:
                subscription_item["quantity"] = quantity
            subscription_items.append(subscription_item)

        if not subscription_items:
            await logger.error("At least one valid item with 'price' is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "At least one valid item with 'price' is required"
                }
            }

        optional_fields: Dict[str, Any] = {}
        for field in ("trial_period_days", "payment_behavior", "coupon", "default_payment_method", "metadata"):
            value = config.get(field)
            if value is not None:
                optional_fields[field] = value

        if config.get("automatic_tax"):
            optional_fields["automatic_tax"] = {"enabled": True}

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        # stripe-python - синхронная библиотека, выполняем её в отдельном потоке,
        # чтобы не блокировать event loop
        try:
            subscription = await asyncio.to_thread(
                stripe.Subscription.create,
                customer=customer_id,
                items=subscription_items,
                api_key=api_key,
                **optional_fields
            )

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": subscription["id"],
                        "status": subscription.get("status"),
                        "customer": subscription.get("customer"),
                        "current_period_end": subscription.get("current_period_end"),
                        "trial_end": subscription.get("trial_end"),
                        "latest_invoice": subscription.get("latest_invoice"),
                        "items_count": len(subscription.get("items", {}).get("data", []))
                    }
                }
            }
        except StripeError as e:
            await logger.error(f"Stripe error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, "http_status", None) or 500,
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
