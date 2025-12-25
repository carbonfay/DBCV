"""YooKassa Create Receipt integration using yookassa SDK.

This integration creates a receipt (check) via the YooKassa SDK `Receipt.create`.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Try to import the SDK directly
try:
    from yookassa import Receipt, Configuration
    from yookassa.domain.exceptions import ApiError
    YOOKASSA_AVAILABLE = True
except ImportError:
    Receipt = None
    Configuration = None
    ApiError = Exception
    YOOKASSA_AVAILABLE = False


class YoukassaCreateReceiptIntegration(BaseIntegration):
    """Создание чека (receipt) в YooKassa через `yookassa` SDK."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="youkassa_create_receipt",
            version="1.0.0",
            name="YouKassa Create Receipt",
            description="Создание фискального чека через YooKassa SDK",
            category="payments",
            icon_s3_key="icons/integrations/youkassa.svg",
            color="#ff6a00",
            config_schema={
                "type": "object",
                "required": ["payment_id", "items"],
                "properties": {
                    "payment_id": {"type": "string", "title": "Payment ID", "description": "ID платежа, для которого формируется чек"},
                    "type": {"type": "string", "title": "Type", "description": "Тип чека: payment/refund"},
                    "send": {"type": "boolean", "title": "Send to customer", "description": "Отправить чек клиенту"},
                    "customer": {"type": "object", "title": "Customer", "description": "Данные покупателя"},
                    "items": {
                        "type": "array",
                        "items": {"type": "object"},
                        "title": "Items",
                        "description": "Список позиций"
                    },
                    "settlements": {
                        "type": "array",
                        "items": {"type": "object"},
                        "title": "Settlements",
                        "description": "Данные расчётов (например, наличные/безналичные)"
                    }
                }
            },
            credentials_provider="other",  # Единый провайдер — как в других интеграциях
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать чек для платежа",
                    "config": {
                        "payment_id": "21b23b5b-000f-5061-a000-0674e49a8c10",
                        "type": "payment",
                        "send": True,
                        "items": [
                            {
                                "description": "Product 1",
                                "quantity": 1,
                                "amount": {"value": "100.00", "currency": "RUB"},
                                "vat_code": "2",
                                "payment_mode": "full_payment",
                                "payment_subject": "commodity"
                            }
                        ]
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
        """Создает чек через yookassa SDK.

        Args:
            config: Параметры для создания чека
            credentials_resolver: Резолвер учетных данных
            bot_id: ID бота
            logger: Логгер

        Returns:
            Результат выполнения: успех или ошибка
        """
        config = {
                        "payment_id": "21b23b5b-000f-5061-a000-0674e49a8c10",
                        "type": "payment",
                        "send": True,
                        "items": [
                            {
                                "description": "Product 1",
                                "quantity": 1,
                                "amount": {"value": "100.00", "currency": "RUB"},
                                "vat_code": "2",
                                "payment_mode": "full_payment",
                                "payment_subject": "commodity"
                            }
                        ]
                    }
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed"
                }
            }

        payment_id = config.get("payment_id")
        items = config.get("items")

        if not payment_id:
            await logger.error("payment_id is required to create a receipt")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required"
                }
            }

        if not items:
            await logger.error("items are required to create a receipt")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items are required"
                }
            }

        # Получаем учетные данные
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",  # Единый провайдер
            strategy="api_key"
        )

        if not creds:
            await logger.error("YouKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YouKassa credentials not found"
                }
            }

        # Извлекаем payload: может быть в `payload` или в корне
        payload = creds.get("payload", creds) if isinstance(creds, dict) else {}
        if not isinstance(payload, dict):
            await logger.error("YouKassa credentials payload is not a dictionary")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Invalid credential format: payload must be a dictionary"
                }
            }

        # Извлекаем ключи (поддержка разных вариантов написания)
        account_id = (
            payload.get("account_id") or
            payload.get("shop_id") or
            payload.get("shopId") or
            payload.get("accountId")
        )
        secret_key = (
            payload.get("secret_key") or
            payload.get("api_key") or
            payload.get("secretKey") or
            payload.get("apiKey") or
            payload.get("secret")
        )
        oauth_token = (
            payload.get("oauth_token") or
            payload.get("auth_token") or
            payload.get("authToken") or
            payload.get("token")
        )

        # Логгируем наличие данных (без вывода значений)
        await logger.debug(f"Found credentials: account_id={bool(account_id)}, secret_key={bool(secret_key)}, oauth_token={bool(oauth_token)}")

        # Настройка аутентификации
        try:
            if oauth_token:
                Configuration.configure_auth_token(oauth_token)
                await logger.info("Configured YooKassa with OAuth token")
            elif account_id and secret_key:
                Configuration.configure(str(account_id), str(secret_key))
                await logger.info(f"Configured YooKassa with account_id={account_id}")
            else:
                await logger.error(
                    "Missing required credentials: need either 'oauth_token' or 'account_id' and 'secret_key'"
                )
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "YouKassa credentials are missing required fields: need either 'oauth_token' or 'account_id' and 'secret_key'"
                    }
                }
        except Exception as e:
            await logger.error(f"Failed to configure YooKassa authentication: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Failed to configure authentication: {str(e)}"
                }
            }

        try:
            # Вызываем SDK для создания чека
            res = Receipt.create(request=config, idempotency_key=str(payment_id))

            # Конвертируем ответ
            if hasattr(res, "to_dict"):
                result = res.to_dict()
            elif hasattr(res, "__dict__"):
                result = {k: v for k, v in vars(res).items() if not k.startswith("_")}
            else:
                result = str(res)

            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except ApiError as e:
            status_code = getattr(e, "http_code", 500)
            await logger.error(f"YouKassa API error creating receipt: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": status_code,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while creating receipt: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
