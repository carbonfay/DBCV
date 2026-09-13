"""Stripe Cancel Subscription интеграция используя официальную библиотеку stripe."""
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


class StripeCancelSubscriptionIntegration(BaseIntegration):
    """Интеграция для отмены подписки (Subscription) в Stripe через официальный SDK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_cancel_subscription",
            version="1.0.0",
            name="Stripe Cancel Subscription",
            description="Отмена подписки клиента в Stripe - немедленно или в конце оплаченного периода",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635BFF",
            config_schema={
                "type": "object",
                "required": ["subscription_id"],
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "title": "Subscription ID",
                        "description": "ID подписки в Stripe (например, sub_ABC123)"
                    },
                    "at_period_end": {
                        "type": "boolean",
                        "title": "Cancel At Period End",
                        "description": "Если включено - подписка отменится в конце оплаченного периода, а не сразу",
                        "default": False
                    },
                    "invoice_now": {
                        "type": "boolean",
                        "title": "Invoice Now",
                        "description": "Выставить счёт за неоплаченное использование немедленно (только при мгновенной отмене)"
                    },
                    "prorate": {
                        "type": "boolean",
                        "title": "Prorate",
                        "description": "Рассчитать пропорциональный возврат/начисление при отмене (только при мгновенной отмене)"
                    },
                    "cancellation_reason": {
                        "type": "string",
                        "title": "Cancellation Reason",
                        "description": "Комментарий/причина отмены подписки для внутреннего учёта"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Немедленная отмена подписки",
                    "config": {
                        "subscription_id": "sub_ABC123",
                        "cancellation_reason": "Пользователь запросил отмену через бота"
                    }
                },
                {
                    "title": "Отмена в конце оплаченного периода",
                    "config": {
                        "subscription_id": "sub_ABC123",
                        "at_period_end": True
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
        Отменяет подписку в Stripe используя stripe.Subscription.delete()
        или stripe.Subscription.modify(cancel_at_period_end=True).

        Args:
            config: Параметры интеграции (subscription_id и опции отмены)
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

        subscription_id = config.get("subscription_id")
        if not subscription_id:
            await logger.error("subscription_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "subscription_id is required"
                }
            }

        at_period_end = bool(config.get("at_period_end", False))
        cancellation_reason = config.get("cancellation_reason")

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        # stripe-python - синхронная библиотека, выполняем её в отдельном потоке,
        # чтобы не блокировать event loop
        try:
            if at_period_end:
                # Отмена в конце периода - подписка остаётся активной до его завершения
                update_fields: Dict[str, Any] = {"cancel_at_period_end": True}
                if cancellation_reason:
                    update_fields["cancellation_details"] = {"comment": cancellation_reason}

                subscription = await asyncio.to_thread(
                    stripe.Subscription.modify,
                    subscription_id,
                    api_key=api_key,
                    **update_fields
                )
            else:
                # Немедленная отмена подписки
                delete_fields: Dict[str, Any] = {}
                if config.get("invoice_now") is not None:
                    delete_fields["invoice_now"] = config.get("invoice_now")
                if config.get("prorate") is not None:
                    delete_fields["prorate"] = config.get("prorate")

                subscription = await asyncio.to_thread(
                    stripe.Subscription.delete,
                    subscription_id,
                    api_key=api_key,
                    **delete_fields
                )

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": subscription["id"],
                        "status": subscription.get("status"),
                        "cancel_at_period_end": subscription.get("cancel_at_period_end"),
                        "canceled_at": subscription.get("canceled_at"),
                        "current_period_end": subscription.get("current_period_end")
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
