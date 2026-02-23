from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from yookassa import Configuration, Refund
    from yookassa.domain.exceptions import ApiError
    YOOKASSA_AVAILABLE = True
except ImportError:
    Configuration = None
    Refund = None
    ApiError = Exception
    YOOKASSA_AVAILABLE = False


class YookassaRefundIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_refund",
            version="1.0.0",
            name="YooKassa Refund",
            description="Возврат платежа по payment_id через YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#4E2E8E",
            config_schema={
                "type": "object",
                "required": ["payment_id", "amount"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "ID платежа для возврата",
                    },
                    "amount": {
                        "type": "string",
                        "title": "Amount",
                        "description": 'Сумма возврата, например "500.00"',
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "default": "RUB",
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Причина возврата",
                    },
                },
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=3.0.0" if YOOKASSA_AVAILABLE else None,
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not YOOKASSA_AVAILABLE:
            await logger.error("yookassa library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "yookassa library is not installed",
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="yookassa", strategy="api_key"
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

        payload = creds.get("payload", {}) or creds
        shop_id = payload.get("shop_id")
        secret_key = payload.get("secret_key")
        if not shop_id or not secret_key:
            await logger.error("shop_id or secret_key not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id or secret_key not found in credentials",
                }
            }

        payment_id = config.get("payment_id")
        amount = config.get("amount")
        currency = config.get("currency", "RUB")
        description = config.get("description")

        if not payment_id or not amount:
            await logger.error("payment_id and amount are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id and amount are required",
                }
            }

        try:
            Configuration.account_id = str(shop_id)
            Configuration.secret_key = str(secret_key)

            data: Dict[str, Any] = {
                "payment_id": str(payment_id),
                "amount": {"value": str(amount), "currency": str(currency)},
            }
            if description:
                data["description"] = str(description)

            refund = Refund.create(data)

            amount_obj = getattr(refund, "amount", None)
            if isinstance(amount_obj, dict):
                amount_value = amount_obj.get("value")
                amount_currency = amount_obj.get("currency")
            else:
                amount_value = getattr(amount_obj, "value", None)
                amount_currency = getattr(amount_obj, "currency", None)
            if amount_value is None:
                amount_value = data["amount"]["value"]
            if amount_currency is None:
                amount_currency = data["amount"]["currency"]

            result_amount = {"value": str(amount_value), "currency": str(amount_currency)}

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": getattr(refund, "id", None),
                        "status": getattr(refund, "status", None),
                        "amount": result_amount,
                        "payment_id": getattr(refund, "payment_id", None),
                        "description": getattr(refund, "description", None),
                    },
                }
            }
        except ApiError as e:  # type: ignore[misc]
            await logger.error(f"YooKassa API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }

