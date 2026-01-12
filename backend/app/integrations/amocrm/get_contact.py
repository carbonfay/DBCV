from __future__ import annotations

import re
from typing import Any

from app.integrations.base_integration import BaseIntegration, IntegrationMetadata
from app.integrations.credentials_resolver import credentials_resolver


class AmoCRMGetContactIntegration(BaseIntegration):
    """
    AmoCRM: Get Contact by ID.

    Credentials strategy: OAuth (amoCRM API).
    """

    metadata = IntegrationMetadata(
        id="amocrm_get_contact",
        version="1.0.0",
        category="crm",
        icon_s3_key="icons/integrations/amocrm.svg",
        config_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Учебный режим: проверить, что интеграция и библиотека установлены "
                        "и код выполняется (без запросов в AmoCRM)."
                    ),
                },
                "contact_id": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "ID контакта в AmoCRM",
                },
            },
            "required": ["contact_id"],
        },
        credentials_provider="amocrm",
        credentials_strategy="oauth",
        library_name="amocrm-api",
    )

    @staticmethod
    def _normalize_subdomain(subdomain_or_domain: str) -> str:
        """
        Accepts:
        - "mycompany"
        - "mycompany.amocrm.ru"
        - "https://mycompany.amocrm.ru"
        """

        v = (subdomain_or_domain or "").strip()
        if not v:
            return ""
        v = re.sub(r"^https?://", "", v, flags=re.IGNORECASE)
        v = v.split("/")[0]
        v = v.split(":")[0]
        # if it's a full domain like "<subdomain>.amocrm.ru" -> extract <subdomain>
        m = re.match(r"^([a-zA-Z0-9-]+)\\.amocrm\\.[a-zA-Z.]+$", v)
        if m:
            return m.group(1)
        return v

    @staticmethod
    def _to_jsonable(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool, list, dict)):
            return value
        # datetime-like
        iso = getattr(value, "isoformat", None)
        if callable(iso):
            try:
                return iso()
            except Exception:
                return str(value)
        return str(value)

    def execute(self, config: dict[str, Any]) -> dict[str, Any]:
        creds = credentials_resolver.get_default_for("amocrm")
        dry_run = bool(config.get("dry_run", False))
        contact_id = int(config["contact_id"])

        try:
            # Library import (explicitly not doing raw HTTP here).
            from amocrm.v2 import Contact  # type: ignore[import-not-found]
            from amocrm.v2 import exceptions as amo_exceptions  # type: ignore[import-not-found]
            from amocrm.v2.tokens import (  # type: ignore[import-not-found]
                MemoryTokensStorage,
                default_token_manager,
            )
            import amocrm  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            return {
                "response": {
                    "ok": False,
                    "error": {
                        "type": e.__class__.__name__,
                        "message": "Missing dependency. Install `amocrm-api` to use this integration.",
                        "details": str(e),
                    },
                }
            }

        # Educational mode: prove the integration runs + SDK is present, without amoCRM account/tokens.
        if dry_run:
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "dry_run": True,
                        "note": "No amoCRM API calls were made. This is a demo execution path.",
                        "library": {
                            "name": "amocrm-api",
                            "import_module": "amocrm",
                            "version": getattr(amocrm, "__version__", None),
                        },
                        "input": {"contact_id": contact_id},
                    },
                }
            }

        try:
            subdomain = self._normalize_subdomain(
                (creds.get("subdomain") or "").strip() or (creds.get("domain") or "").strip()
            )
            client_id = (creds.get("client_id") or "").strip()
            client_secret = (creds.get("client_secret") or "").strip()
            redirect_url = (creds.get("redirect_uri") or creds.get("redirect_url") or "").strip()
            access_token = (creds.get("access_token") or "").strip()
            refresh_token = (creds.get("refresh_token") or "").strip()

            if not subdomain:
                raise ValueError("Missing AMOCRM_SUBDOMAIN (or AMOCRM_DOMAIN)")
            if not (client_id and client_secret and redirect_url):
                raise ValueError("Missing AMOCRM_CLIENT_ID/AMOCRM_CLIENT_SECRET/AMOCRM_REDIRECT_URI")
            if not (access_token or refresh_token):
                raise ValueError("Missing AMOCRM_ACCESS_TOKEN or AMOCRM_REFRESH_TOKEN")

            storage = MemoryTokensStorage()
            storage.save_tokens(access_token or "", refresh_token or "")

            # Configure token manager used by SDK internals (requests inside SDK).
            default_token_manager(
                client_id=client_id,
                client_secret=client_secret,
                subdomain=subdomain,
                redirect_url=redirect_url,
                storage=storage,
            )

            # If access_token is missing, try to refresh using refresh_token (SDK internal method).
            if not access_token and refresh_token:
                new_access, new_refresh = default_token_manager._get_new_tokens()  # noqa: SLF001
                storage.save_tokens(new_access, new_refresh)

            # Fetch contact via the SDK (no manual HTTP here).
            contact = Contact.objects.get(object_id=contact_id)

            # Serialize a stable subset (library objects may be non-JSON-serializable).
            result: dict[str, Any] = {
                "id": getattr(contact, "id", None),
                "name": getattr(contact, "name", None),
                "first_name": getattr(contact, "first_name", None),
                "last_name": getattr(contact, "last_name", None),
                "created_at": self._to_jsonable(getattr(contact, "created_at", None)),
                "updated_at": self._to_jsonable(getattr(contact, "updated_at", None)),
                "responsible_user_id": getattr(getattr(contact, "_data", {}), "get", lambda *_: None)(
                    "responsible_user_id"
                ),
            }

            # Optional fields if present
            company = getattr(contact, "company", None)
            if company is not None:
                result["company"] = {
                    "id": getattr(company, "id", None),
                    "name": getattr(company, "name", None),
                }

            tags = getattr(contact, "tags", None)
            if tags is not None:
                try:
                    result["tags"] = [{"id": t.id, "name": t.name} for t in tags]  # type: ignore[iteration-over-optional]
                except Exception:
                    result["tags"] = self._to_jsonable(tags)

            # Raw custom fields payload if present (amoCRM v4: custom_fields_values)
            try:
                result["custom_fields_values"] = contact._data.get("custom_fields_values")  # type: ignore[attr-defined]
            except Exception:
                pass

            return {"response": {"ok": True, "result": result}}

        except amo_exceptions.BaseModuleException as e:
            return {
                "response": {
                    "ok": False,
                    "error": {"type": e.__class__.__name__, "message": str(e)},
                }
            }
        except Exception as e:
            # Library errors + validation errors are wrapped into a unified shape.
            return {
                "response": {
                    "ok": False,
                    "error": {"type": e.__class__.__name__, "message": str(e)},
                }
            }


