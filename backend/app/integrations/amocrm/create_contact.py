"""AmoCRM Create Contact integration using httpx for direct API calls."""
from typing import Dict, Any, Optional
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class AmoCrmCreateContactIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_create_contact",
            version="1.0.0",
            name="AmoCRM Create Contact",
            description="Create a contact in AmoCRM using direct httpx requests",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#ff6c00",
            config_schema={
                "type": "object",
                "required": ["subdomain", "name"],
                "properties": {
                    "subdomain": {
                        "type": "string",
                        "title": "Subdomain",
                        "description": "AmoCRM subdomain (e.g. mycompany) or full host (mycompany.amocrm.ru)"
                    },
                    "name": {
                        "type": "string",
                        "title": "Contact Name",
                        "description": "Name of the contact to create"
                    },
                    "custom_fields": {
                        "type": "array",
                        "title": "Custom Fields",
                        "description": "Array of custom_fields_values objects for AmoCRM",
                    }
                }
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name=None,
            examples=[
                {
                    "title": "Create contact",
                    "config": {"subdomain": "mycompany", "name": "John Doe", "custom_fields": []}
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

        # Config
        subdomain = config.get("subdomain") or payload.get("base_domain")
        # normalize subdomain: allow either 'mycompany' or 'mycompany.amocrm.ru'
        if subdomain and subdomain.endswith(".amocrm.ru"):
            base_domain = subdomain
        elif subdomain:
            base_domain = f"{subdomain}.amocrm.ru"
        else:
            await logger.error("subdomain is required in config or credentials payload")
            return {"response": {"ok": False, "error_code": 400, "description": "subdomain is required"}}

        name = config.get("name")
        if not name:
            await logger.error("name is required in config")
            return {"response": {"ok": False, "error_code": 400, "description": "name is required"}}

        custom_fields = config.get("custom_fields")

        access_token = payload.get("access_token")
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        refresh_token = payload.get("refresh_token")
        redirect_uri = payload.get("redirect_uri")

        # If no access_token, try to refresh it using refresh_token
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

        # Create contact
        try:
            url = f"https://{base_domain}/api/v4/contacts"
            headers = {"Authorization": f"Bearer {access_token}"}
            body = [{"name": name}]
            if custom_fields is not None:
                body[0]["custom_fields_values"] = custom_fields

            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(url, headers=headers, json=body)
                r.raise_for_status()
                j = r.json()

            # Try to extract created contact
            contact = None
            if isinstance(j, dict):
                contact = j.get("_embedded", {}).get("contacts", [None])[0]
                # fallback for simple responses
                if not contact:
                    # sometimes API returns array directly
                    contacts = j.get("contacts") or (j.get("_embedded", {}).get("contacts"))
                    if contacts and isinstance(contacts, list):
                        contact = contacts[0]
            if not contact and isinstance(j, list) and len(j) > 0:
                contact = j[0]

            if not contact:
                # If structure unexpected, return raw json
                return {"response": {"ok": True, "result": j}}

            return {"response": {"ok": True, "result": {"id": contact.get("id"), "name": contact.get("name")}}}
        except httpx.HTTPStatusError as e:
            await logger.error(f"AmoCRM API error: {e}")
            code = e.response.status_code if e.response is not None else 500
            return {"response": {"ok": False, "error_code": code, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error when creating AmoCRM contact: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
