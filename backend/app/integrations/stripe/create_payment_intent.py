"""Stripe Create Payment Intent интеграция используя stripe библиотеку."""
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


class StripeCreatePaymentIntentIntegration(BaseIntegration):
    """Интеграция для создания платежных намерений в Stripe."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_create_payment_intent",
            version="1.0.0",
            name="Stripe Create Payment Intent",
            description="Создание платежного намерения в Stripe для обработки платежей",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#6772E5",
            config_schema={
                "type": "object",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {
                        "type": "integer",
                        "title": "Amount",
                        "description": "Сумма платежа в наименьших единицах (например, центы для USD)",
                        "minimum": 1
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "description": "Код валюты (например, usd, eur, rub)",
                        "default": "usd"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание платежа"
                    },
                    "receipt_email": {
                        "type": "string",
                        "title": "Receipt Email",
                        "description": "Email для отправки квитанции"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Создание платежа на 10 долларов",
                    "config": {
                        "amount": 1000,  # 10.00 USD в центах
                        "currency": "usd",
                        "description": "Оплата за товар",
                        "receipt_email": "{$user.email$}"
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

        # Получаем параметры из config
        amount = config.get("amount")
        currency = config.get("currency", "usd")
        description = config.get("description")
        receipt_email = config.get("receipt_email")

        if not amount:
            await logger.error("amount is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount is required"
                }
            }

        # Устанавливаем API ключ
        stripe.api_key = secret_key

        # Подготовим параметры для создания платежного намерения
        payment_intent_params = {
            "amount": int(amount),
            "currency": str(currency).lower(),
        }

        if description:
            payment_intent_params["description"] = str(description)
        if receipt_email:
            payment_intent_params["receipt_email"] = str(receipt_email)

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем платежное намерение
            intent = stripe.PaymentIntent.create(**payment_intent_params)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": intent.id,
                        "amount": intent.amount,
                        "currency": intent.currency,
                        "status": intent.status,
                        "client_secret": intent.client_secret,  # Этот параметр нужен для подтверждения на клиенте
                        "created": intent.created
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

