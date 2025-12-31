"""PayPal Get Order integration using PayPal REST API via httpx.

This integration fetches an order by its ID using PayPal's Orders API (v2).
Credentials should provide `client_id` and `client_secret` (strategy: "oauth").
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    httpx = None
    HTTPX_AVAILABLE = False


class PaypalGetOrderIntegration(BaseIntegration):
    """Интеграция получения заказа PayPal по order_id."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="paypal_get_order",
            version="1.0.0",
            name="PayPal Get Order",
            description="Fetch PayPal order details by order ID using PayPal REST API",
            category="payments",
            icon_s3_key="icons/integrations/paypal.svg",
            color="#003087",
            config_schema={
                "type": "object",
                "required": ["order_id"],
                "properties": {
                    "order_id": {
                        "type": "string",
                        "title": "Order ID",
                        "description": "PayPal order ID to fetch"
                    },
                    "environment": {
                        "type": "string",
                        "title": "Environment",
                        "enum": ["sandbox", "live"],
                        "default": "sandbox",
                        "description": "PayPal environment to use (overrides credentials environment if provided)"
                    }
                }
            },
            credentials_provider="paypal",
            credentials_strategy="oauth",
            library_name="httpx>=0.23.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Get order",
                    "config": {"order_id": "REPLACE_WITH_ORDER_ID", "environment": "sandbox"}
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Fetch order using PayPal REST API via `httpx`.

        Expected credentials payload contains `client_id` and `client_secret`.
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        # Resolve credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="paypal",
            strategy="oauth"
        )

        if not creds:
            await logger.error("PayPal credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "PayPal credentials not found"
                }
            }

        payload = creds.get("payload", {}) if isinstance(creds, dict) else creds
        if not_payload := (payload is None or payload == {}):
            payload = creds

        client_id = payload.get("client_id") or payload.get("clientId")
        client_secret = payload.get("client_secret") or payload.get("clientSecret")
        if not client_id or not client_secret:
            await logger.error(f"PayPal client_id/client_secret not found in credentials. Keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "client_id or client_secret not found in credentials"
                }
            }

        order_id = config.get("order_id")
        if not order_id:
            await logger.error("order_id is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "order_id is required"
                }
            }

        # Determine environment: config overrides credentials
        env = (config.get("environment") or payload.get("environment") or "sandbox").lower()
        if env not in ("sandbox", "live"):
            env = "sandbox"

        base_host = "api-m.sandbox.paypal.com" if env == "sandbox" else "api-m.paypal.com"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Get access token
                token_url = f"https://{base_host}/v1/oauth2/token"
                headers = {"Accept": "application/json"}
                data = {"grant_type": "client_credentials"}
                token_resp = await client.post(token_url, auth=(client_id, client_secret), data=data, headers=headers)
                if token_resp.status_code != 200:
                    await logger.error(f"Failed to obtain PayPal token: {token_resp.status_code} {token_resp.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": token_resp.status_code,
                            "description": "Failed to obtain PayPal access token",
                            "details": token_resp.text
                        }
                    }

                token_json = token_resp.json()
                access_token = token_json.get("access_token")
                if not access_token:
                    await logger.error(f"No access_token in token response: {token_json}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 500,
                            "description": "No access_token in PayPal token response",
                            "details": token_json
                        }
                    }

                # Fetch order
                order_url = f"https://{base_host}/v2/checkout/orders/{order_id}"
                order_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
                order_resp = await client.get(order_url, headers=order_headers)
                if order_resp.status_code not in (200, 201):
                    await logger.error(f"PayPal get order failed: {order_resp.status_code} {order_resp.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": order_resp.status_code,
                            "description": "Failed to fetch PayPal order",
                            "details": order_resp.text
                        }
                    }

                order_json = order_resp.json()
                return {
                    "response": {
                        "ok": True,
                        "result": order_json
                    }
                }

        except httpx.HTTPError as e:
            await logger.error(f"HTTP error when calling PayPal: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error in PayPal get_order: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
