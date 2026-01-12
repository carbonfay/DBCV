from __future__ import annotations

import time
import uuid
from typing import Any

from app.integrations.base_integration import BaseIntegration, IntegrationMetadata
from app.integrations.credentials_resolver import credentials_resolver


class PayPalCreatePayoutIntegration(BaseIntegration):
    """
    PayPal: Create Payout (Payouts API).

    Credentials strategy: OAuth (client_id + client_secret).
    """

    metadata = IntegrationMetadata(
        id="paypal_create_payout",
        version="1.0.0",
        category="payments",
        icon_s3_key="icons/integrations/paypal.svg",
        config_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Учебный режим: проверить, что интеграция и библиотека установлены "
                        "(без запросов в PayPal)."
                    ),
                },
                "sender_batch_id": {
                    "type": "string",
                    "minLength": 1,
                    "description": (
                        "Уникальный ID батча. Если не задан — будет сгенерирован автоматически."
                    ),
                },
                "email_subject": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Тема письма получателю (PayPal уведомление).",
                },
                "email_message": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Текст письма получателю (PayPal уведомление).",
                },
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "recipient_type": {
                                "type": "string",
                                "enum": ["EMAIL", "PHONE", "PAYPAL_ID"],
                                "default": "EMAIL",
                                "description": "Тип получателя (обычно EMAIL).",
                            },
                            "receiver": {
                                "type": "string",
                                "minLength": 1,
                                "description": "Email/phone/PayPal ID получателя (в зависимости от recipient_type).",
                            },
                            "amount": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "value": {
                                        "type": ["string", "number"],
                                        "description": "Сумма выплаты.",
                                    },
                                    "currency": {
                                        "type": "string",
                                        "minLength": 3,
                                        "maxLength": 3,
                                        "default": "USD",
                                        "description": "Валюта (ISO 4217), например USD.",
                                    },
                                },
                                "required": ["value", "currency"],
                            },
                            "note": {"type": "string", "description": "Заметка получателю."},
                            "sender_item_id": {
                                "type": "string",
                                "minLength": 1,
                                "description": "Уникальный ID позиции внутри батча.",
                            },
                        },
                        "required": ["recipient_type", "receiver", "amount", "sender_item_id"],
                    },
                },
            },
            "required": ["items"],
        },
        credentials_provider="paypal",
        credentials_strategy="oauth",
        library_name="paypal-payouts-sdk",
    )

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [PayPalCreatePayoutIntegration._jsonable(v) for v in value]
        if isinstance(value, dict):
            return {str(k): PayPalCreatePayoutIntegration._jsonable(v) for k, v in value.items()}

        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            try:
                return PayPalCreatePayoutIntegration._jsonable(to_dict())
            except Exception:
                pass

        d = getattr(value, "__dict__", None)
        if isinstance(d, dict) and d:
            public = {k: v for k, v in d.items() if not str(k).startswith("_")}
            if public:
                return PayPalCreatePayoutIntegration._jsonable(public)

        iso = getattr(value, "isoformat", None)
        if callable(iso):
            try:
                return iso()
            except Exception:
                pass

        return str(value)

    @staticmethod
    def _make_batch_id(explicit: str | None) -> str:
        v = (explicit or "").strip()
        if v:
            return v
        # PayPal requires uniqueness; keep deterministic prefix for observability.
        return f"dbcv_{int(time.time())}_{uuid.uuid4().hex}"

    def execute(self, config: dict[str, Any]) -> dict[str, Any]:
        creds = credentials_resolver.get_default_for("paypal")
        dry_run = bool(config.get("dry_run", False))

        try:
            from paypalpayoutssdk.core import (  # type: ignore[import-not-found]
                LiveEnvironment,
                PayPalHttpClient,
                SandboxEnvironment,
            )
            from paypalpayoutssdk.payouts import PayoutsPostRequest  # type: ignore[import-not-found]
            from paypalhttp.http_error import HttpError  # type: ignore[import-not-found]
            import paypalpayoutssdk as paypalpayoutssdk_module  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": e.__class__.__name__,
                        "message": "Missing dependency. Install `paypal-payouts-sdk` to use this integration.",
                        "details": str(e),
                    },
                }
            }

        if dry_run:
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "dry_run": True,
                        "note": "No PayPal API calls were made. This is a demo execution path.",
                        "library": {
                            "name": "paypal-payouts-sdk",
                            "import_module": "paypalpayoutssdk",
                            "version": getattr(paypalpayoutssdk_module, "__version__", None),
                        },
                    },
                }
            }

        try:
            client_id = (creds.get("client_id") or "").strip()
            client_secret = (creds.get("client_secret") or "").strip()
            mode = (creds.get("mode") or "sandbox").strip().lower()

            if not client_id:
                raise ValueError("Missing PAYPAL_CLIENT_ID")
            if not client_secret:
                raise ValueError("Missing PAYPAL_CLIENT_SECRET")
            if mode not in {"sandbox", "live"}:
                raise ValueError("PAYPAL_MODE must be 'sandbox' or 'live'")

            environment = (
                SandboxEnvironment(client_id=client_id, client_secret=client_secret)
                if mode == "sandbox"
                else LiveEnvironment(client_id=client_id, client_secret=client_secret)
            )
            client = PayPalHttpClient(environment)

            items = config.get("items")
            if not isinstance(items, list) or not items:
                raise ValueError("`items` must be a non-empty array")

            sender_batch_id = self._make_batch_id(config.get("sender_batch_id"))
            body: dict[str, Any] = {
                "sender_batch_header": {
                    "sender_batch_id": sender_batch_id,
                },
                "items": items,
            }

            if config.get("email_subject"):
                body["sender_batch_header"]["email_subject"] = str(config["email_subject"])
            if config.get("email_message"):
                body["sender_batch_header"]["email_message"] = str(config["email_message"])

            req = PayoutsPostRequest()
            req.request_body(body)

            resp = client.execute(req)

            result: dict[str, Any] = {
                "status_code": getattr(resp, "status_code", None),
                "headers": self._jsonable(getattr(resp, "headers", None)),
                "result": self._jsonable(getattr(resp, "result", None)),
            }
            return {"response": {"ok": True, "result": result}}

        except HttpError as e:
            details = {
                "status_code": getattr(e, "status_code", None),
                "headers": self._jsonable(getattr(e, "headers", None)),
                "message": getattr(e, "message", None),
                "error": self._jsonable(getattr(e, "error", None)),
            }
            return {
                "response": {
                    "ok": False,
                    "error": {"type": e.__class__.__name__, "message": str(e), "details": details},
                }
            }
        except Exception as e:
            return {"response": {"ok": False, "error": {"type": e.__class__.__name__, "message": str(e)}}}


