"""Stripe Create Customer интеграция используя stripe библиотеку."""
from typing import Dict, Any
from uuid import UUID
import asyncio

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


class StripeCreateCustomerIntegration(BaseIntegration):
    """Интеграция для создания клиента в Stripe (POST /v1/customers)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_create_customer",
            version="1.0.0",
            name="Stripe Create Customer",
            description="Создание клиента в Stripe через официальную библиотеку",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635bff",
            config_schema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "title": "Email",
                        "description": "Email клиента"
                    },
                    "name": {
                        "type": "string",
                        "title": "Name",
                        "description": "Имя клиента"
                    },
                    "phone": {
                        "type": "string",
                        "title": "Phone",
                        "description": "Телефон клиента"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание клиента"
                    },
                    "metadata": {
                        "type": "object",
                        "title": "Metadata",
                        "description": "Дополнительные метаданные клиента (JSON)"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Клиент с email",
                    "config": {
                        "email": "customer@example.com",
                        "name": "Test Customer"
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

        # Получаем secret_key из credentials
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
                    "description": "Stripe secret_key not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        secret_key = payload.get("secret_key") or payload.get("api_key") or payload.get("token")
        if not secret_key:
            await logger.error(f"secret_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "secret_key not found in credentials"
                }
            }

        # Получаем параметры из config
        email = config.get("email")
        name = config.get("name")
        phone = config.get("phone")
        description = config.get("description")
        metadata = config.get("metadata")

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ (stripe синхронная — оборачиваем в to_thread)
        def _create_customer() -> dict:
            stripe.api_key = secret_key
            params = {}
            if email:
                params["email"] = str(email)
            if name:
                params["name"] = str(name)
            if phone:
                params["phone"] = str(phone)
            if description:
                params["description"] = str(description)
            if metadata:
                params["metadata"] = metadata
            customer = stripe.Customer.create(**params)
            return {
                "id": customer.get("id"),
                "email": customer.get("email"),
                "name": customer.get("name"),
                "phone": customer.get("phone"),
                "description": customer.get("description"),
                "created": customer.get("created")
            }

        try:
            result = await asyncio.to_thread(_create_customer)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except stripe.StripeError as e:
            await logger.error(f"Stripe error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.http_status if hasattr(e, "http_status") else 400,
                    "description": e.user_message if hasattr(e, "user_message") and e.user_message else str(e)
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
