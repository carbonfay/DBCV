"""YooKassa Create Receipt интеграция используя yookassa библиотеку."""

from typing import Any, Dict
from uuid import UUID

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from yookassa import Configuration, Receipt
    from yookassa.domain.exceptions import ApiError

    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Receipt = None
    ApiError = Exception


class YookassaCreateReceiptIntegration(BaseIntegration):
    """Интеграция для создания чека в YooKassa."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_create_receipt",
            version="1.0.0",
            name="YooKassa Create Receipt",
            description="Создание чека в системе YooKassa для отправки клиенту",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#8B5CF6",
            config_schema={
                "type": "object",
                "required": ["payment_id", "items", "settlements"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа, для которого создается чек",
                    },
                    "customer_full_name": {
                        "type": "string",
                        "title": "Customer Full Name",
                        "description": "ФИО покупателя",
                    },
                    "customer_email": {
                        "type": "string",
                        "title": "Customer Email",
                        "description": "Email покупателя (рекомендуется)",
                        "format": "email",
                    },
                    "customer_phone": {
                        "type": "string",
                        "title": "Customer Phone",
                        "description": "Телефон покупателя (рекомендуется)",
                        "pattern": "^\\+?[1-9]\\d{1,14}$",
                    },
                    "customer_inn": {
                        "type": "string",
                        "title": "Customer INN",
                        "description": "ИНН покупателя",
                        "pattern": "^\\d{10}|\\d{12}$",
                    },
                    "items": {
                        "type": "array",
                        "title": "Items",
                        "description": "Список товаров/услуг в чеке",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": [
                                "description",
                                "quantity",
                                "amount",
                                "vat_code",
                                "payment_mode",
                                "payment_subject",
                            ],
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "title": "Description",
                                    "description": "Наименование товара",
                                },
                                "quantity": {
                                    "type": "number",
                                    "title": "Quantity",
                                    "description": "Количество товара",
                                    "minimum": 0.001,
                                },
                                "amount": {
                                    "type": "object",
                                    "title": "Amount",
                                    "description": "Стоимость товара",
                                    "required": ["value", "currency"],
                                    "properties": {
                                        "value": {
                                            "type": "string",
                                            "title": "Value",
                                            "description": "Сумма (например '100.00')",
                                            "pattern": "^\\d+(\\.\\d{1,2})?$",
                                        },
                                        "currency": {
                                            "type": "string",
                                            "title": "Currency",
                                            "description": "Валюта",
                                            "enum": ["RUB", "USD", "EUR"],
                                            "default": "RUB",
                                        },
                                    },
                                },
                                "vat_code": {
                                    "type": "integer",
                                    "title": "VAT Code",
                                    "description": "Код НДС (1-6)",
                                    "enum": [1, 2, 3, 4, 5, 6],
                                },
                                "payment_mode": {
                                    "type": "string",
                                    "title": "Payment Mode",
                                    "description": "Признак способа расчета",
                                    "enum": [
                                        "full_prepayment",
                                        "partial_prepayment",
                                        "advance",
                                        "full_payment",
                                        "partial_payment",
                                        "credit",
                                        "credit_payment",
                                    ],
                                    "default": "full_prepayment",
                                },
                                "payment_subject": {
                                    "type": "string",
                                    "title": "Payment Subject",
                                    "description": "Признак предмета расчета",
                                    "enum": [
                                        "commodity",
                                        "excise",
                                        "job",
                                        "service",
                                        "gambling_bet",
                                        "gambling_prize",
                                        "lottery",
                                        "lottery_prize",
                                        "intellectual_activity",
                                        "payment",
                                        "agent_commission",
                                        "composite",
                                        "another",
                                    ],
                                    "default": "commodity",
                                },
                            },
                        },
                    },
                    "settlements": {
                        "type": "array",
                        "title": "Settlements",
                        "description": "Расчеты по чеку",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["type", "amount"],
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "title": "Settlement Type",
                                    "description": "Тип расчета",
                                    "enum": [
                                        "cashless",
                                        "prepayment",
                                        "postpayment",
                                        "other",
                                    ],
                                    "default": "cashless",
                                },
                                "amount": {
                                    "type": "object",
                                    "title": "Amount",
                                    "description": "Сумма расчета",
                                    "required": ["value", "currency"],
                                    "properties": {
                                        "value": {
                                            "type": "string",
                                            "title": "Value",
                                            "description": "Сумма (например '100.00')",
                                            "pattern": "^\\d+(\\.\\d{1,2})?$",
                                        },
                                        "currency": {
                                            "type": "string",
                                            "title": "Currency",
                                            "description": "Валюта",
                                            "enum": ["RUB", "USD", "EUR"],
                                            "default": "RUB",
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "send": {
                        "type": "boolean",
                        "title": "Send",
                        "description": "Отправлять ли чек клиенту",
                        "default": True,
                    },
                    "internet": {
                        "type": "boolean",
                        "title": "Internet",
                        "description": "Признак торговли через интернет",
                        "default": True,
                    },
                },
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
            examples=[
                {
                    "title": "Простой чек после платежа",
                    "description": "Создание чека для платежа без товаров. Подходит для сценария 'Сначала платеж, потом чек'",
                    "config": {
                        "payment_id": "24b94598-000f-5000-9000-1b68e7b15f3f",
                        "customer_email": "customer@example.com",
                        "items": [
                            {
                                "description": "Товар 1",
                                "quantity": 1.0,
                                "amount": {"value": "100.00", "currency": "RUB"},
                                "vat_code": 2,
                                "payment_mode": "full_prepayment",
                                "payment_subject": "commodity",
                            }
                        ],
                        "settlements": [
                            {
                                "type": "cashless",
                                "amount": {"value": "100.00", "currency": "RUB"},
                            }
                        ],
                    },
                },
                {
                    "title": "Чек с полными данными клиента",
                    "description": "Полный чек с максимальной информацией о клиенте и товарах",
                    "config": {
                        "payment_id": "24b94598-000f-5000-9000-1b68e7b15f3f",
                        "customer_full_name": "Иванов Иван Иванович",
                        "customer_email": "ivan@example.com",
                        "customer_phone": "79000000000",
                        "items": [
                            {
                                "description": "Консультация",
                                "quantity": 1.0,
                                "amount": {"value": "5000.00", "currency": "RUB"},
                                "vat_code": 1,
                                "payment_mode": "full_payment",
                                "payment_subject": "service",
                            },
                            {
                                "description": "Материалы",
                                "quantity": 2.0,
                                "amount": {"value": "150.00", "currency": "RUB"},
                                "vat_code": 2,
                                "payment_mode": "full_payment",
                                "payment_subject": "commodity",
                            },
                        ],
                        "settlements": [
                            {
                                "type": "cashless",
                                "amount": {"value": "5300.00", "currency": "RUB"},
                            }
                        ],
                        "send": True,
                        "internet": True,
                    },
                },
                {
                    "title": "Чек зачета предоплаты",
                    "description": "Чек для зачета предварительно внесенной предоплаты",
                    "config": {
                        "payment_id": "24b94598-000f-5000-9000-1b68e7b15f3f",
                        "customer_email": "customer@example.com",
                        "items": [
                            {
                                "description": "Товар с предоплатой",
                                "quantity": 1.0,
                                "amount": {"value": "1000.00", "currency": "RUB"},
                                "vat_code": 2,
                                "payment_mode": "full_payment",
                                "payment_subject": "commodity",
                            }
                        ],
                        "settlements": [
                            {
                                "type": "prepayment",
                                "amount": {"value": "1000.00", "currency": "RUB"},
                            }
                        ],
                        "send": True,
                        "internet": True,
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
        payment_id = config.get("payment_id")
        customer_full_name = config.get("customer_full_name")
        customer_email = config.get("customer_email")
        customer_phone = config.get("customer_phone")
        customer_inn = config.get("customer_inn")
        items = config.get("items", [])
        settlements = config.get("settlements", [])
        send = config.get("send", True)
        internet = config.get("internet", True)

        if not payment_id:
            await logger.error("payment_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required",
                }
            }

        if not items:
            await logger.error("items array is required and cannot be empty")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items array is required and cannot be empty",
                }
            }

        if not settlements:
            await logger.error("settlements array is required and cannot be empty")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "settlements array is required and cannot be empty",
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Настраиваем конфигурацию YooKassa
            Configuration.account_id = account_id
            Configuration.secret_key = secret_key

            await logger.info(
                f"Configuring YooKassa with account_id: {account_id[:8]}..."
            )

            # Подготавливаем данные для создания чека
            receipt_data = {
                "payment_id": payment_id,
                "type": "payment",
                "send": send,
                "items": items,
                "settlements": settlements,
                "internet": internet,
            }

            # Добавляем данные клиента если они есть
            customer = {}
            if customer_full_name:
                customer["full_name"] = customer_full_name
            if customer_email:
                customer["email"] = customer_email
            if customer_phone:
                customer["phone"] = customer_phone
            if customer_inn:
                customer["inn"] = customer_inn

            if customer:
                receipt_data["customer"] = customer

            await logger.info(f"Creating receipt for payment_id: {payment_id}")
            await logger.info(
                f"Receipt data structure: {len(items)} items, {len(settlements)} settlements"
            )

            # Создаем чек
            receipt = Receipt.create(receipt_data)

            # Проверяем, что чек создался успешно
            if not receipt:
                await logger.error("Receipt creation returned None")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "Receipt creation failed - returned None",
                    }
                }

            # Возвращаем упрощенный результат чтобы избежать проблем с сериализацией
            import json

            # Пытаемся преобразовать receipt в строку, а потом обратно в dict
            try:
                receipt_str = str(receipt)
                await logger.info(f"Receipt object as string: {receipt_str[:200]}...")
            except:
                pass

            # Создаем простой результат без сложных объектов YooKassa
            result = {
                "id": str(getattr(receipt, "id", "")),
                "type": str(getattr(receipt, "type", "")),
                "payment_id": str(getattr(receipt, "payment_id", "")),
                "status": str(getattr(receipt, "status", "")),
                "items_count": len(getattr(receipt, "items", [])),
                "customer_info": "customer data provided"
                if getattr(receipt, "customer", None)
                else "no customer data",
                "receipt_created": True,
                "message": "Receipt created successfully in YooKassa. Check YooKassa dashboard for full details.",
            }

            await logger.info(f"Receipt created successfully: {result['id']}")

            return {
                "response": {
                    "ok": True,
                    "result": result,
                }
            }
        except ApiError as e:
            await logger.error(f"YooKassa API error: {e}")
            await logger.error(
                f"Error details: type={type(e)}, args={getattr(e, 'args', 'N/A')}"
            )

            # Try different possible attribute names for error code
            error_code = 400
            if hasattr(e, "http_code"):
                error_code = e.http_code
            elif hasattr(e, "status_code"):
                error_code = e.status_code
            elif hasattr(e, "code"):
                error_code = e.code

            # Log additional error context
            await logger.error(f"Payment ID: {payment_id}")
            await logger.error(f"Items count: {len(items)}")
            await logger.error(f"Settlements count: {len(settlements)}")

            return {
                "response": {
                    "ok": False,
                    "error_code": error_code,
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            await logger.error(f"Error type: {type(e)}")
            await logger.error(f"Payment ID: {payment_id}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
