"""PayPal Create Subscription integration using paypalrestsdk."""
from __future__ import annotations

import os
from typing import Any, Dict
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import paypalrestsdk
    try:
        from paypalrestsdk import Resource
    except Exception:
        from paypalrestsdk.resource import Resource
    try:
        from paypalrestsdk import exceptions as paypal_exceptions
    except Exception:
        paypal_exceptions = None
    PAYPAL_SDK_AVAILABLE = True
except ImportError:
    paypalrestsdk = None
    Resource = None
    paypal_exceptions = None
    PAYPAL_SDK_AVAILABLE = False


class PayPalSDKError(Exception):
    """Base error for PayPal SDK handling."""


class PayPalConnectionError(PayPalSDKError):
    """Network error when calling PayPal SDK."""


class PayPalUnauthorized(PayPalSDKError):
    """Auth error when calling PayPal SDK."""


class PayPalServerError(PayPalSDKError):
    """Server error returned by PayPal SDK."""


class PayPalResourceNotFound(PayPalSDKError):
    """Resource not found error from PayPal SDK."""


if paypal_exceptions:
    PayPalConnectionError = getattr(paypal_exceptions, "ConnectionError", PayPalConnectionError)
    PayPalUnauthorized = getattr(paypal_exceptions, "UnauthorizedAccess", PayPalUnauthorized)
    PayPalServerError = getattr(paypal_exceptions, "ServerError", PayPalServerError)
    PayPalResourceNotFound = getattr(paypal_exceptions, "ResourceNotFound", PayPalResourceNotFound)


if PAYPAL_SDK_AVAILABLE and Resource is not None:
    class BillingSubscription(Resource):
        """PayPal Billing Subscription resource."""
        path = "/v1/billing/subscriptions"
else:
    BillingSubscription = None


PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "")


class PaypalCreateSubscriptionIntegration(BaseIntegration):
    """Create a PayPal subscription using paypalrestsdk."""

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
            library_name="paypalrestsdk>=1.13.0" if PAYPAL_SDK_AVAILABLE else None,
            examples=[
                {
                    "title": "Create subscription",
                    "config": {
                        "plan_id": "P-123456789",
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
        if not PAYPAL_SDK_AVAILABLE or BillingSubscription is None:
            await logger.error("paypalrestsdk library is not available")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "missing_library",
                        "message": "paypalrestsdk library is not installed"
                    }
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="paypal",
            strategy="oauth"
        )

        payload = {}
        if creds:
            payload = creds.get("payload", {}) or creds

        client_id = payload.get("client_id") or payload.get("clientId") or PAYPAL_CLIENT_ID
        client_secret = payload.get("client_secret") or payload.get("clientSecret") or PAYPAL_CLIENT_SECRET
        mode = payload.get("mode") or payload.get("environment") or PAYPAL_MODE or "sandbox"
        base_url = payload.get("base_url") or payload.get("api_base") or PAYPAL_BASE_URL

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

        api_config = {
            "mode": mode,
            "client_id": client_id,
            "client_secret": client_secret
        }
        if base_url:
            api_config["api_base"] = base_url

        try:
            api = paypalrestsdk.Api(api_config)
            subscription = BillingSubscription(subscription_payload, api=api)
            created = subscription.create()
            if not created:
                error_details = getattr(subscription, "error", None) or {
                    "message": "Unknown PayPal API error"
                }
                await logger.error(f"PayPal API error: {error_details}")
                return {
                    "response": {
                        "ok": False,
                        "error": {
                            "type": "api_error",
                            "message": "PayPal API returned an error",
                            "details": error_details
                        }
                    }
                }

            result = subscription.to_dict() if hasattr(subscription, "to_dict") else subscription.__dict__
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except PayPalUnauthorized as e:
            await logger.error(f"PayPal auth error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "auth_error",
                        "message": str(e)
                    }
                }
            }
        except PayPalConnectionError as e:
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
        except PayPalServerError as e:
            await logger.error(f"PayPal server error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "server_error",
                        "message": str(e)
                    }
                }
            }
        except PayPalResourceNotFound as e:
            await logger.error(f"PayPal resource not found: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": "not_found",
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
