"""YooKassa Create Refund интеграция используя yookassa библиотеку."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from yookassa import Configuration, Refund
    from yookassa.domain.exceptions import ApiError, BadRequestError, UnauthorizedException
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    Configuration = None
    Refund = None
    ApiError = Exception
    BadRequestError = Exception
    UnauthorizedException = Exception


class YooKassaCreateRefundIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_create_refund",
            version="1.0.0",
            name="YooKassa Create Refund",
            description="Создание возврата в YooKassa по payment_id",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#7F3FFF",
            config_schema={
                "type": "object",
                "required": ["payment_id", "amount"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа, по которому создаётся возврат"
                    },
                    "amount": {
                        "type": "string",
                        "title": "Amount",
                        "description": "Сумма возврата, например 100.00"
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "default": "RUB"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "maxLength": 250
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="yookassa>=3.0.0" if YOOKASSA_AVAILABLE else None
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed"
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )

        if not creds:
            await logger.error("YooKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials not found"
                }
            }

        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        shop_id = payload.get("shop_id")
        secret_key = payload.get("secret_key")
        if not shop_id or not secret_key:
            await logger.error("shop_id or secret_key not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id or secret_key not found in credentials"
                }
            }

        payment_id = config.get("payment_id")
        amount_raw = config.get("amount")
        currency = config.get("currency") or "RUB"
        description = config.get("description")

        if not payment_id or amount_raw is None:
            await logger.error("payment_id and amount are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id and amount are required"
                }
            }

        try:
            amount_decimal = Decimal(str(amount_raw)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, ValueError):
            await logger.error("amount must be a valid number")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount must be a valid number"
                }
            }

        if description is not None and len(description) > 250:
            await logger.error("description must be at most 250 characters")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "description must be at most 250 characters"
                }
            }

        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key

        refund_payload: Dict[str, Any] = {
            "amount": {
                "value": str(amount_decimal),
                "currency": str(currency)
            },
            "payment_id": str(payment_id)
        }
        if description:
            refund_payload["description"] = str(description)

        try:
            refund = Refund.create(refund_payload)
            refund_amount = getattr(refund, "amount", None)
            refund_amount_value = getattr(refund_amount, "value", None) if refund_amount else None
            refund_amount_currency = getattr(refund_amount, "currency", None) if refund_amount else None

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "refund_id": getattr(refund, "id", None),
                        "status": getattr(refund, "status", None),
                        "amount": {
                            "value": refund_amount_value,
                            "currency": refund_amount_currency
                        },
                        "payment_id": getattr(refund, "payment_id", None),
                        "description": getattr(refund, "description", None)
                    }
                }
            }
        except BadRequestError as e:
            await logger.error(f"YooKassa bad request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": str(e)
                }
            }
        except UnauthorizedException as e:
            await logger.error(f"YooKassa unauthorized error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": str(e)
                }
            }
        except ApiError as e:
            await logger.error(f"YooKassa API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
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
