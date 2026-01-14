"""AmoCRM Update Contact integration using httpx for direct API calls."""
from typing import Dict, Any, Optional
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class AmoCrmUpdateContactIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_update_contact",
            version="1.0.0",
            name="AmoCRM Update Contact",
            description="Update an existing contact in AmoCRM using direct httpx requests",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#ff6c00",
            config_schema={
                "type": "object",
                "required": ["subdomain", "id"],
                "properties": {
                    "subdomain": {"type": "string", "title": "Subdomain"},
                    "id": {"type": "number", "title": "Contact ID"},
                    "name": {"type": "string", "title": "Contact Name"},
                    "custom_fields": {"type": "array", "title": "Custom Fields"}
                }
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name=None,
            examples=[
                {"title": "Update contact name", "config": {"subdomain": "mycompany", "id": 12345, "name": "John Updated"}}
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        # Get credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="amocrm",
            strategy="oauth"
        )

        if not creds:
            await logger.error("AmoCRM credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "AmoCRM credentials not found"}}

        payload = creds.get("payload", {}) or creds

        subdomain = config.get("subdomain") or payload.get("base_domain")
        if subdomain and subdomain.endswith(".amocrm.ru"):
            base_domain = subdomain
        elif subdomain:
            base_domain = f"{subdomain}.amocrm.ru"
        else:
            await logger.error("subdomain is required in config or credentials payload")
            return {"response": {"ok": False, "error_code": 400, "description": "subdomain is required"}}

        contact_id = config.get("id")
        if not contact_id:
            await logger.error("id is required in config")
            return {"response": {"ok": False, "error_code": 400, "description": "id is required"}}

        name = config.get("name")
        custom_fields = config.get("custom_fields")
        # Treat empty lists/strings as not provided
        if not name and not custom_fields:
            await logger.error("At least one of name or custom_fields must be provided")
            return {"response": {"ok": False, "error_code": 400, "description": "At least one of name or custom_fields must be provided"}}

        access_token = payload.get("access_token")
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        refresh_token = payload.get("refresh_token")
        redirect_uri = payload.get("redirect_uri")

        # If no access_token, try to refresh
        if not access_token and refresh_token and client_id and client_secret:
            try:
                token_url = f"https://{base_domain}/oauth2/access_token"
                token_payload = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }
                if redirect_uri:
                    token_payload["redirect_uri"] = redirect_uri

                async with httpx.AsyncClient(timeout=20) as client:
                    r = await client.post(token_url, json=token_payload)
                    r.raise_for_status()
                    j = r.json()
                access_token = j.get("access_token")
            except httpx.HTTPError as e:
                await logger.error(f"Failed to refresh AmoCRM token: {e}")
                return {"response": {"ok": False, "error_code": 401, "description": f"token refresh failed: {str(e)}"}}

        if not access_token:
            await logger.error("access_token not found in credentials and could not be refreshed")
            return {"response": {"ok": False, "error_code": 401, "description": "access_token not found"}}

        # Build update payload (object)
        update_data: Dict[str, Any] = {}
        if name is not None:
            update_data["name"] = name
        # Only include custom_fields when explicitly provided and non-empty
        if custom_fields is not None and (isinstance(custom_fields, (list, tuple)) and len(custom_fields) > 0):
            update_data["custom_fields_values"] = custom_fields

        try:
            url = f"https://{base_domain}/api/v4/contacts/{contact_id}"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.patch(url, headers=headers, json=update_data)
                r.raise_for_status()
                j = r.json()

            # AmoCRM usually returns the updated contact object for PATCH /contacts/{id}
            contact = None
            if isinstance(j, dict) and "id" in j:
                contact = j
            else:
                # Fallback: try embedded contacts or top-level list
                embedded = (j.get("_embedded") if isinstance(j, dict) else None) or {}
                contacts = embedded.get("contacts") or (j.get("contacts") if isinstance(j, dict) else None)
                if isinstance(contacts, list) and contacts:
                    contact = contacts[0]
                elif isinstance(j, list) and j:
                    contact = j[0]

            if not contact:
                return {"response": {"ok": True, "result": j}}

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": contact.get("id"),
                        "name": contact.get("name"),
                        "updated_at": contact.get("updated_at")
                    }
                }
            }
        except httpx.HTTPStatusError as e:
            await logger.error(f"AmoCRM API error: {e}")
            code = e.response.status_code if e.response is not None else 500
            return {"response": {"ok": False, "error_code": code, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error when updating AmoCRM contact: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
