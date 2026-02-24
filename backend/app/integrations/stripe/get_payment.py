from typing import Dict, Any, Optional, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import stripe
    from stripe.error import StripeError
    STRIPE_AVAILABLE = True
except Exception:
    STRIPE_AVAILABLE = False
    stripe = None  # type: ignore
    class StripeError(Exception):  # type: ignore
        pass


def _get_attr(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


class StripeGetPaymentIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="stripe_get_payment",
            version="1.0.0",
            name="Stripe Get Payment",
            description="Получить информацию о платеже (Charge) по ID через Stripe API",
            category="payments",
            icon_s3_key="icons/integrations/stripe.svg",
            color="#635BFF",
            config_schema={
                "type": "object",
                "required": ["charge_id"],
                "properties": {
                    "charge_id": {
                        "type": "string",
                        "title": "Charge ID"
                    },
                    "expand": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "Expand"
                    }
                }
            },
            credentials_provider="stripe",
            credentials_strategy="api_key",
            library_name="stripe",
            examples=[
                {
                    "title": "Получить платеж",
                    "config": {
                        "charge_id": "ch_1234567890"
                    }
                },
                {
                    "title": "Получить платеж с expand",
                    "config": {
                        "charge_id": "ch_1234567890",
                        "expand": ["balance_transaction", "customer"]
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

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload and isinstance(creds, dict):
            payload = creds

        api_key = payload.get("api_key")
        if not api_key:
            await logger.error(f"api_key not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials"
                }
            }

        charge_id = config.get("charge_id")
        expand: Optional[List[str]] = config.get("expand")
        if not charge_id:
            await logger.error("charge_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "charge_id is required"
                }
            }

        try:
            stripe.api_key = api_key
            if expand and isinstance(expand, list) and len(expand) > 0:
                charge = stripe.Charge.retrieve(charge_id, expand=expand)  # type: ignore
            else:
                charge = stripe.Charge.retrieve(charge_id)  # type: ignore

            result_charge = charge.to_dict() if hasattr(charge, "to_dict") else (charge if isinstance(charge, dict) else None)

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": _get_attr(charge, "id"),
                        "amount": _get_attr(charge, "amount"),
                        "currency": _get_attr(charge, "currency"),
                        "status": _get_attr(charge, "status"),
                        "paid": _get_attr(charge, "paid"),
                        "charge": result_charge
                    }
                }
            }
        except StripeError as e:  # type: ignore
            await logger.error(f"Stripe error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
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

