from __future__ import annotations

from typing import Any

from app.integrations.base_integration import BaseIntegration, IntegrationMetadata
from app.integrations.credentials_resolver import credentials_resolver


class YooKassaGetPaymentListIntegration(BaseIntegration):
    """
    YooKassa: Get Payment List.

    Credentials strategy: API key (shop/account id + secret key).
    """

    metadata = IntegrationMetadata(
        id="yookassa_get_payment_list",
        version="1.0.0",
        category="payments",
        icon_s3_key="icons/integrations/yookassa.svg",
        config_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Учебный режим: проверить, что интеграция и библиотека установлены "
                        "(без запросов в YooKassa)."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                    "description": "Количество платежей в ответе (1..100).",
                },
                "cursor": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Курсор для пагинации (значение `next_cursor` из предыдущего ответа).",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "waiting_for_capture", "succeeded", "canceled"],
                    "description": "Фильтр по статусу платежа.",
                },
                "created_at_gte": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Фильтр: created_at >= (RFC3339).",
                },
                "created_at_lt": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Фильтр: created_at < (RFC3339).",
                },
            },
        },
        credentials_provider="yookassa",
        credentials_strategy="api_key",
        library_name="yookassa",
    )

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [YooKassaGetPaymentListIntegration._jsonable(v) for v in value]
        if isinstance(value, dict):
            return {str(k): YooKassaGetPaymentListIntegration._jsonable(v) for k, v in value.items()}

        # common SDK patterns
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            try:
                return YooKassaGetPaymentListIntegration._jsonable(to_dict())
            except Exception:
                pass

        as_dict = getattr(value, "dict", None)
        if callable(as_dict):
            try:
                return YooKassaGetPaymentListIntegration._jsonable(as_dict())
            except Exception:
                pass

        # dataclass-ish / simple objects
        d = getattr(value, "__dict__", None)
        if isinstance(d, dict) and d:
            # filter private fields for stability
            public = {k: v for k, v in d.items() if not str(k).startswith("_")}
            if public:
                return YooKassaGetPaymentListIntegration._jsonable(public)

        iso = getattr(value, "isoformat", None)
        if callable(iso):
            try:
                return iso()
            except Exception:
                pass

        return str(value)

    def execute(self, config: dict[str, Any]) -> dict[str, Any]:
        creds = credentials_resolver.get_default_for("yookassa")
        dry_run = bool(config.get("dry_run", False))

        try:
            from yookassa import Configuration, Payment  # type: ignore[import-not-found]
            from yookassa.domain.exceptions import ApiError  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": e.__class__.__name__,
                        "message": "Missing dependency. Install `yookassa` to use this integration.",
                        "details": str(e),
                    },
                }
            }

        # Educational mode: prove the integration runs + SDK is present.
        if dry_run:
            import yookassa as yookassa_module  # type: ignore[import-not-found]

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "dry_run": True,
                        "note": "No YooKassa API calls were made. This is a demo execution path.",
                        "library": {
                            "name": "yookassa",
                            "import_module": "yookassa",
                            "version": getattr(yookassa_module, "__version__", None),
                        },
                    },
                }
            }

        try:
            account_id = (creds.get("shop_id") or creds.get("account_id") or "").strip()
            secret_key = (creds.get("secret_key") or "").strip()
            if not account_id:
                raise ValueError("Missing YOOKASSA_SHOP_ID (or YOOKASSA_ACCOUNT_ID)")
            if not secret_key:
                raise ValueError("Missing YOOKASSA_SECRET_KEY")

            # Configure SDK (no manual HTTP; SDK does requests internally).
            Configuration.account_id = account_id
            Configuration.secret_key = secret_key

            params: dict[str, Any] = {}
            if "limit" in config and config["limit"] is not None:
                params["limit"] = int(config["limit"])
            if config.get("cursor"):
                params["cursor"] = str(config["cursor"])
            if config.get("status"):
                params["status"] = str(config["status"])
            if config.get("created_at_gte"):
                params["created_at.gte"] = str(config["created_at_gte"])
            if config.get("created_at_lt"):
                params["created_at.lt"] = str(config["created_at_lt"])

            payments_list = Payment.list(params)

            # SDK returns an object like: {type: "list", items: [...], next_cursor: "..."}
            result: dict[str, Any] = {
                "type": getattr(payments_list, "type", "list"),
                "next_cursor": getattr(payments_list, "next_cursor", None),
                "items": [],
            }

            items = getattr(payments_list, "items", None)
            if items is not None:
                result["items"] = self._jsonable(items)
            else:
                # fallback: serialize whole response if "items" is not exposed
                result = self._jsonable(payments_list)

            return {"response": {"ok": True, "result": result}}

        except ApiError as e:
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": e.__class__.__name__,
                        "message": str(e),
                        "details": self._jsonable(getattr(e, "__dict__", None) or None),
                    },
                }
            }
        except Exception as e:
            return {"response": {"ok": False, "error": {"type": e.__class__.__name__, "message": str(e)}}}


