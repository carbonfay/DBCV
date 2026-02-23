from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from yookassa import Configuration, Receipt
    try:
        from yookassa.exceptions import ApiError, ApiRequestError
    except Exception:
        ApiError = Exception
        ApiRequestError = Exception
    YOOKASSA_AVAILABLE = True
except Exception:
    Configuration = None
    Receipt = None
    ApiError = Exception
    ApiRequestError = Exception
    YOOKASSA_AVAILABLE = False


class YooKassaCreateReceiptIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_create_receipt",
            version="1.0.0",
            name="YooKassa Create Receipt",
            description="Создание кассового чека в YooKassa (POST /v3/receipts)",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#2EAE60",
            config_schema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "title": "Items",
                        "items": {"type": "object"}
                    },
                    "send": {
                        "type": "boolean",
                        "title": "Send to customer",
                        "default": True
                    },
                    "email": {
                        "type": "string",
                        "title": "Customer email"
                    },
                    "phone": {
                        "type": "string",
                        "title": "Customer phone"
                    },
                    "tax_system_code": {
                        "type": "integer",
                        "title": "Tax system code"
                    },
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID"
                    },
                    "external_id": {
                        "type": "string",
                        "title": "External ID"
                    },
                    "settlements": {
                        "type": "array",
                        "title": "Settlements",
                        "items": {"type": "object"}
                    },
                    "idempotence_key": {
                        "type": "string",
                        "title": "Idempotence Key"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            library_name="yookassa>=2.3.0" if YOOKASSA_AVAILABLE else None,
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
            provider="yookassa",
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

        payload_creds = creds.get("payload", {}) or creds
        shop_id = payload_creds.get("shop_id") or payload_creds.get("account_id")
        secret_key = payload_creds.get("secret_key") or payload_creds.get("api_key")
        if not shop_id or not secret_key:
            await logger.error("Missing shop_id or secret_key in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "shop_id or secret_key missing in credentials"
                }
            }

        Configuration.account_id = str(shop_id)
        Configuration.secret_key = str(secret_key)

        payment_id: Optional[str] = config.get("payment_id")
        send: Optional[bool] = config.get("send", True)
        email: Optional[str] = config.get("email")
        phone: Optional[str] = config.get("phone")
        tax_system_code: Optional[int] = config.get("tax_system_code")
        external_id: Optional[str] = config.get("external_id")
        items = config.get("items") or []
        settlements = config.get("settlements")
        idem_key = config.get("idempotence_key") or str(uuid4())

        try:
            if payment_id:
                data: Dict[str, Any] = {"payment_id": payment_id}
                if send is not None:
                    data["send"] = bool(send)
                if email or phone:
                    customer: Dict[str, Any] = {}
                    if email:
                        customer["email"] = email
                    if phone:
                        customer["phone"] = phone
                    data["customer"] = customer
                if external_id:
                    data["external_id"] = external_id
                if tax_system_code is not None:
                    data["tax_system_code"] = tax_system_code
                result = Receipt.create(data, idempotence_key=idem_key)
            else:
                if not settlements:
                    await logger.error("settlements is required for standalone receipt")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "settlements is required for standalone receipt"
                        }
                    }
                customer: Dict[str, Any] = {}
                if email:
                    customer["email"] = email
                if phone:
                    customer["phone"] = phone
                if not customer:
                    await logger.error("customer (email or phone) is required for standalone receipt")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "customer with email or phone is required for standalone receipt"
                        }
                    }
                data = {
                    "type": "payment",
                    "send": bool(send),
                    "items": items,
                    "settlements": settlements,
                    "customer": customer
                }
                if tax_system_code is not None:
                    data["tax_system_code"] = tax_system_code
                if external_id:
                    data["external_id"] = external_id
                result = Receipt.create(data, idempotence_key=idem_key)

            await logger.info(f"YooKassa receipt created: {result}")
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except ApiError as e:
            await logger.error(f"YooKassa API error: {e}")
            code = getattr(e, "status_code", None) or getattr(e, "code", None) or 502
            return {
                "response": {
                    "ok": False,
                    "error_code": code,
                    "description": str(e)
                }
            }
        except ApiRequestError as e:
            await logger.error(f"YooKassa library error: {e}")
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
