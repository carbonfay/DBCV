"""PayPal Create Subscription integration using httpx."""
from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False


PAYPAL_SANDBOX_API_BASE = "https://api-m.sandbox.paypal.com"
PAYPAL_LIVE_API_BASE = "https://api-m.paypal.com"


def _safe_json(response):
    try:
        return response.json()
    except Exception:
        text = getattr(response, "text", "")
        return {"raw": text} if text else None


class PaypalCreateSubscriptionIntegration(BaseIntegration):
    """Create a PayPal subscription using httpx."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="paypal_create_subscription",
            version="1.0.0",
            name="PayPal Create Subscription",
            description="Create a billing subscription in PayPal",
            category="payments",
            icon_s3_key="icons/integrations/paypal.svg",
            color="#003087",
            config_schema={
                "type": "object",
                "required": ["plan_id"],
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "title": "Plan ID",
                        "description": "PayPal plan ID"
                    },
                    "start_time": {
                        "type": "string",
                        "title": "Start Time",
                        "description": "Subscription start time (ISO 8601)"
                    },
                    "quantity": {
                        "type": "string",
                        "title": "Quantity",
                        "description": "Quantity for the subscription"
                    },
                    "subscriber": {
                        "type": "object",
                        "title": "Subscriber",
                        "properties": {
                            "email_address": {
                                "type": "string",
                                "title": "Subscriber Email"
                            },
                            "name": {
                                "type": "object",
                                "title": "Subscriber Name",
                                "properties": {
                                    "given_name": {
                                        "type": "string",
                                        "title": "Given Name"
                                    },
                                    "surname": {
                                        "type": "string",
                                        "title": "Surname"
                                    }
                                }
                            }
                        }
                    },
                    "application_context": {
                        "type": "object",
                        "title": "Application Context",
                        "properties": {
                            "brand_name": {
                                "type": "string",
                                "title": "Brand Name"
                            },
                            "locale": {
                                "type": "string",
                                "title": "Locale"
                            },
                            "shipping_preference": {
                                "type": "string",
                                "title": "Shipping Preference"
                            },
                            "user_action": {
                                "type": "string",
                                "title": "User Action"
                            },
                            "return_url": {
                                "type": "string",
                                "title": "Return URL"
                            },
                            "cancel_url": {
                                "type": "string",
                                "title": "Cancel URL"
                            }
                        }
                    },
                    "custom_id": {
                        "type": "string",
                        "title": "Custom ID"
                    },
                    "payment_method": {
                        "type": "object",
                        "title": "Payment Method",
                        "description": "Payment method details if supported"
                    },
                    "shipping_amount": {
                        "type": "object",
                        "title": "Shipping Amount",
                        "description": "Shipping amount details"
                    },
                    "plan_overridden": {
                        "type": "object",
                        "title": "Plan Overridden",
                        "description": "Override plan data if supported"
                    },
                    "billing_info": {
                        "type": "object",
                        "title": "Billing Info",
                        "description": "Billing info if supported"
                    }
                }
            },
            credentials_provider="paypal",
            credentials_strategy="oauth",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Create subscription",
                    "config": {
                        "plan_id": "P-123456789",
                        "start_time": "2026-12-01T12:00:00Z",
                        "quantity": "1",
                        "subscriber": {
                            "email_address": "customer@example.com",
                            "name": {
                                "given_name": "Jane",
                                "surname": "Doe"
                            }
                        },
                        "application_context": {
                            "brand_name": "DBCV",
                            "locale": "en-US",
                            "user_action": "SUBSCRIBE_NOW",
                            "return_url": "https://example.com/success",
                            "cancel_url": "https://example.com/cancel"
                        },
                        "custom_id": "order-12345",
                        "payment_method": {
                            "payer_selected": "PAYPAL",
                            "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                        },
                        "shipping_amount": {
                            "currency_code": "USD",
                            "value": "10.00"
                        }
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
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "missing_library",
                        "message": "httpx library is not installed"
                    }
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="oauth"
        )

        payload = {}
        if creds:
            payload = creds.get("payload", {}) or creds

        client_id = payload.get("client_id") or payload.get("clientId")
        client_secret = payload.get("client_secret") or payload.get("clientSecret")
        mode = payload.get("mode") or payload.get("environment") or "sandbox"
        base_url = payload.get("base_url") or payload.get("api_base")

        if not base_url:
            base_url = PAYPAL_LIVE_API_BASE if mode in ("live", "production") else PAYPAL_SANDBOX_API_BASE

        if not client_id or not client_secret:
            await logger.error("PayPal credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "credentials_missing",
                        "message": "PayPal client_id/client_secret not found"
                    }
                }
            }

        plan_id = config.get("plan_id")
        if not plan_id:
            await logger.error("plan_id is required")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "invalid_config",
                        "message": "plan_id is required"
                    }
                }
            }

        subscription_payload: Dict[str, Any] = {
            "plan_id": str(plan_id)
        }

        for field in [
            "start_time",
            "quantity",
            "subscriber",
            "application_context",
            "custom_id",
            "payment_method",
            "shipping_amount",
            "plan_overridden",
            "billing_info"
        ]:
            value = config.get(field)
            if value is not None:
                subscription_payload[field] = value

        token_url = f"{base_url}/v1/oauth2/token"
        subscription_url = f"{base_url}/v1/billing/subscriptions"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                token_response = await client.post(
                    token_url,
                    data={"grant_type": "client_credentials"},
                    auth=(client_id, client_secret),
                    headers={"Accept": "application/json"}
                )
                token_data = _safe_json(token_response)
                if token_response.status_code >= 400:
                    error_type = "auth_error" if token_response.status_code in (401, 403) else "token_error"
                    await logger.error(f"PayPal token error: {token_data}")
                    return {
                        "response": {
                            "ok": False,
                            "error": {
                                "type": error_type,
                                "message": "PayPal token request failed",
                                "status_code": token_response.status_code,
                                "details": token_data
                            }
                        }
                    }

                access_token = token_data.get("access_token") if token_data else None
                if not access_token:
                    await logger.error("PayPal access_token not found in response")
                    return {
                        "response": {
                            "ok": False,
                            "error": {
                                "type": "token_error",
                                "message": "access_token not found in PayPal response",
                                "details": token_data
                            }
                        }
                    }

                subscription_response = await client.post(
                    subscription_url,
                    json=subscription_payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                subscription_data = _safe_json(subscription_response)
                if subscription_response.status_code >= 400:
                    await logger.error(f"PayPal API error: {subscription_data}")
                    return {
                        "response": {
                            "ok": False,
                            "error": {
                                "type": "api_error",
                                "message": "PayPal API returned an error",
                                "status_code": subscription_response.status_code,
                                "details": subscription_data
                            }
                        }
                    }

                return {
                    "response": {
                        "ok": True,
                        "result": subscription_data
                    }
                }
        except httpx.RequestError as e:
            await logger.error(f"PayPal network error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "network_error",
                        "message": str(e)
                    }
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected PayPal error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "unexpected_error",
                        "message": str(e)
                    }
                }
            }
