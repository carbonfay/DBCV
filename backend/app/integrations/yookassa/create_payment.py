"""YooKassa Create Payment интеграция используя yookassa библиотеку."""

from typing import Any, Dict
from uuid import UUID

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from yookassa import Configuration, Payment
    from yookassa.domain.exceptions import ApiError

    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Payment = None
    ApiError = Exception


class YookassaCreatePaymentIntegration(BaseIntegration):
    """Интеграция для создания платежа в YooKassa."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_create_payment",
            version="1.0.0",
            name="YooKassa Create Payment",
            description="Создание нового платежа в системе YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#8B5CF6",
            config_schema={
                "type": "object",
                "required": ["amount", "currency", "return_url"],
                "properties": {
                    "amount": {
                        "type": "string",
                        "title": "Amount",
                        "description": "Сумма платежа (например, '100.00')",
                        "pattern": r"^\d+(\.\d{1,2})?$",
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "description": "Валюта платежа",
                        "enum": ["RUB", "USD", "EUR"],
                        "default": "RUB",
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Описание платежа",
                    },
                    "return_url": {
                        "type": "string",
                        "title": "Return URL",
                        "description": "URL для возврата после оплаты",
                        "format": "uri",
                    },
                    "capture": {
                        "type": "boolean",
                        "title": "Auto Capture",
                        "description": "Автоматическое списание средств",
                        "default": True,
                    },
                    "metadata": {
                        "type": "object",
                        "title": "Metadata",
                        "description": "Дополнительные данные для платежа",
                        "additionalProperties": {"type": "string"},
                    },
                },
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Простой платеж",
                    "config": {
                        "amount": "100.00",
                        "currency": "RUB",
                        "description": "Оплата заказа №123",
                        "return_url": "https://example.com/success",
                    },
                },
                {
                    "title": "Платеж с метаданными",
                    "config": {
                        "amount": "250.50",
                        "currency": "RUB",
                        "description": "Покупка товара",
                        "return_url": "https://example.com/success",
                        "capture": True,
                        "metadata": {"order_id": "12345", "user_id": "67890"},
                    },
                },
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя библиотеку yookassa.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed",
                }
            }

        # Получаем credentials из credentials_resolver
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="other", strategy="api_key"
        )

        if not creds:
            await logger.error("YooKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials not found",
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        account_id = payload.get("account_id")
        secret_key = payload.get("secret_key")

        if not account_id or not secret_key:
            await logger.error(
                f"account_id or secret_key not found in credentials. Available keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "account_id and secret_key are required in credentials",
                }
            }

        # Получаем параметры из config
        amount = config.get("amount")
        currency = config.get("currency", "RUB")
        description = config.get("description")
        return_url = config.get("return_url")
        capture = config.get("capture", True)
        metadata = config.get("metadata", {})

        if not amount or not return_url:
            await logger.error("amount and return_url are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount and return_url are required",
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Настраиваем конфигурацию YooKassa
            Configuration.account_id = account_id
            Configuration.secret_key = secret_key

            # Подготавливаем данные для создания платежа
            payment_data = {
                "amount": {"value": str(amount), "currency": currency},
                "confirmation": {"type": "redirect", "return_url": return_url},
                "capture": capture,
            }

            # Добавляем описание если оно есть
            if description:
                payment_data["description"] = description

            # Добавляем метаданные если они есть
            if metadata:
                payment_data["metadata"] = metadata

            # Создаем платеж
            payment = Payment.create(payment_data)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": payment.id,
                        "status": payment.status,
                        "amount": {
                            "value": payment.amount.value,
                            "currency": payment.amount.currency,
                        }
                        if payment.amount
                        else None,
                        "description": payment.description,
                        "confirmation": {
                            "type": payment.confirmation.type,
                            "confirmation_url": payment.confirmation.confirmation_url,
                        }
                        if payment.confirmation
                        else None,
                        "created_at": payment.created_at.isoformat()
                        if payment.created_at
                        and hasattr(payment.created_at, "isoformat")
                        else str(payment.created_at)
                        if payment.created_at
                        else None,
                        "paid": payment.paid,
                        "refundable": payment.refundable,
                        "metadata": payment.metadata
                        if hasattr(payment, "metadata")
                        else {},
                        "test": payment.test if hasattr(payment, "test") else False,
                    },
                }
            }
        except ApiError as e:
            await logger.error(f"YooKassa API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, "http_code", 400),
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
