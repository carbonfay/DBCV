"""Stripe Update Customer интеграция используя официальную библиотеку stripe."""
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


class StripeUpdateCustomerIntegration(BaseIntegration):
    """Интеграция для обновления данных клиента (Customer) в Stripe через официальный SDK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_update_customer",
            version="1.0.0",
            name="Stripe Update Customer",
            description="Обновление данных клиента (email, имя, телефон, метаданные) в Stripe",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635BFF",
            config_schema={
                "type": "object",
                "required": ["customer_id"],
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "title": "Customer ID",
                        "description": "ID клиента в Stripe (например, cus_ABC123)"
                    },
                    "email": {
                        "type": "string",
                        "title": "Email",
                        "description": "Новый email клиента"
                    },
                    "name": {
                        "type": "string",
                        "title": "Name",
                        "description": "Новое имя клиента"
                    },
                    "phone": {
                        "type": "string",
                        "title": "Phone",
                        "description": "Новый номер телефона клиента"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Внутреннее описание клиента (не видно клиенту)"
                    },
                    "metadata": {
                        "type": "object",
                        "title": "Metadata",
                        "description": "Произвольные метаданные клиента в формате ключ-значение"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe>=7.0.0" if STRIPE_AVAILABLE else None,
            examples=[
                {
                    "title": "Обновление email клиента после подтверждения",
                    "config": {
                        "customer_id": "cus_ABC123",
                        "email": "{$user.email$}"
                    }
                },
                {
                    "title": "Обновление контактных данных и метаданных",
                    "config": {
                        "customer_id": "cus_ABC123",
                        "name": "{$user.full_name$}",
                        "phone": "{$user.phone$}",
                        "metadata": {"telegram_chat_id": "{$user.telegram_chat_id$}"}
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
        Обновляет клиента Stripe используя stripe.Customer.modify().

        Args:
            config: Параметры интеграции (customer_id и обновляемые поля)
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

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
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
        if not customer_id:
            await logger.error("customer_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "customer_id is required"
                }
            }

        update_fields = {}
        for field in ("email", "name", "phone", "description", "metadata"):
            value = config.get(field)
            if value is not None:
                update_fields[field] = value

        if not update_fields:
            await logger.error("At least one field to update must be provided")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "At least one of email, name, phone, description, metadata is required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        # stripe-python - синхронная библиотека, выполняем её в отдельном потоке,
        # чтобы не блокировать event loop
        try:
            customer = await asyncio.to_thread(
                stripe.Customer.modify,
                customer_id,
                api_key=api_key,
                **update_fields
            )

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": customer["id"],
                        "email": customer.get("email"),
                        "name": customer.get("name"),
                        "phone": customer.get("phone"),
                        "description": customer.get("description"),
                        "metadata": customer.get("metadata")
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
