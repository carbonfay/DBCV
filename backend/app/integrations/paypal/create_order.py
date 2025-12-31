"""PayPal Create Order integration using PayPal REST API via httpx.

Creates an order (v2 Orders API). Credentials must provide `client_id` and `client_secret`.
"""
from typing import Dict, Any, List, Optional
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


class PaypalCreateOrderIntegration(BaseIntegration):
    """Интеграция создания заказа PayPal."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="paypal_create_order",
            version="1.0.0",
            name="PayPal Create Order",
            description="Create a PayPal order via Orders API (v2).",
            category="payments",
            icon_s3_key="icons/integrations/paypal.svg",
            color="#003087",
            config_schema={
                "type": "object",
                "required": ["intent", "purchase_units"],
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": ["CAPTURE", "AUTHORIZE"],
                        "default": "CAPTURE",
                        "title": "Intent",
                        "description": "Order intent: CAPTURE or AUTHORIZE"
                    },
                    "purchase_units": {
                        "type": "array",
                        "title": "Purchase units",
                        "items": {
                            "type": "object",
                            "required": ["amount"],
                            "properties": {
                                "reference_id": {"type": "string"},
                                "description": {"type": "string"},
                                "amount": {
                                    "type": "object",
                                    "required": ["currency_code", "value"],
                                    "properties": {
                                        "currency_code": {"type": "string"},
                                        "value": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "application_context": {
                        "type": "object",
                        "properties": {
                            "return_url": {"type": "string"},
                            "cancel_url": {"type": "string"},
                            "brand_name": {"type": "string"},
                            "landing_page": {"type": "string"},
                            "user_action": {"type": "string"}
                        }
                    }
                }
            },
            credentials_provider="paypal",
            credentials_strategy="oauth",
            library_name="httpx>=0.23.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Create order (simple)",
                    "config": {
                        "intent": "CAPTURE",
                        "purchase_units": [
                            {"amount": {"currency_code": "USD", "value": "10.00"}}
                        ],
                        "application_context": {
                            "return_url": "https://example.com/return",
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
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {"response": {"ok": False, "error_code": 500, "description": "httpx library is not installed"}}

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="paypal",
            strategy="oauth"
        )

        if not creds:
            await logger.error("PayPal credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "PayPal credentials not found"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else creds
        if not_payload := (payload is None or payload == {}):
            payload = creds

        client_id = payload.get("client_id") or payload.get("clientId")
        client_secret = payload.get("client_secret") or payload.get("clientSecret")
        if not client_id or not client_secret:
            await logger.error("PayPal client_id/client_secret not found in credentials")
            return {"response": {"ok": False, "error_code": 401, "description": "client_id or client_secret not found in credentials"}}

        # Build request body
        intent = config.get("intent", "CAPTURE")
        purchase_units = config.get("purchase_units")
        if not purchase_units or not isinstance(purchase_units, list):
            await logger.error("purchase_units is required and must be a list")
            return {"response": {"ok": False, "error_code": 400, "description": "purchase_units is required"}}

        application_context = config.get("application_context")

        env = (config.get("environment") or payload.get("environment") or "sandbox").lower()
        if env not in ("sandbox", "live"):
            env = "sandbox"
        base_host = "api-m.sandbox.paypal.com" if env == "sandbox" else "api-m.paypal.com"

        body: Dict[str, Any] = {"intent": intent, "purchase_units": purchase_units}
        if application_context:
            body["application_context"] = application_context

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Prepare auth (use BasicAuth if available for clarity)
                try:
                    auth = httpx.BasicAuth(client_id, client_secret)
                except Exception:
                    auth = (client_id, client_secret)

                await logger.info("Requesting PayPal access token")
                token_url = f"https://{base_host}/v1/oauth2/token"
                headers = {"Accept": "application/json"}
                data = {"grant_type": "client_credentials"}
                token_resp = await client.post(token_url, auth=auth, data=data, headers=headers)
                if token_resp.status_code != 200:
                    await logger.error(f"Failed to obtain PayPal token: {token_resp.status_code} {token_resp.text}")
                    return {"response": {"ok": False, "error_code": token_resp.status_code, "description": "Failed to obtain PayPal access token", "details": token_resp.text}}

                try:
                    token_json = token_resp.json()
                except Exception:
                    token_json = {"raw": token_resp.text}

                access_token = token_json.get("access_token")
                if not access_token:
                    await logger.error(f"No access_token in token response: {token_json}")
                    return {"response": {"ok": False, "error_code": 500, "description": "No access_token in PayPal token response", "details": token_json}}

                # Create order
                order_url = f"https://{base_host}/v2/checkout/orders"
                order_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                order_resp = await client.post(order_url, json=body, headers=order_headers)
                if order_resp.status_code not in (200, 201):
                    await logger.error(f"PayPal create order failed: {order_resp.status_code} {order_resp.text}")
                    return {"response": {"ok": False, "error_code": order_resp.status_code, "description": "Failed to create PayPal order", "details": order_resp.text}}

                try:
                    order_json = order_resp.json()
                except Exception:
                    order_json = {"raw": order_resp.text}

                order_id = order_json.get("id") or order_json.get("result", {}).get("id")
                await logger.info(f"PayPal order created: {order_id}")
                return {"response": {"ok": True, "result": order_json}}

        except httpx.HTTPError as e:
            await logger.error(f"HTTP error when calling PayPal: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error in PayPal create_order: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
        