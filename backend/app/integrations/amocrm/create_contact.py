from typing import Dict, Any
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
            description="Create a contact in AmoCRM using the REST API.",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#ff8c00",
            config_schema={
                "type": "object",
                "required": ["subdomain", "name"],
                "properties": {
                    "subdomain": {
                        "type": "string",
                        "title": "Subdomain",
                        "description": "AmoCRM subdomain (e.g. mycompany).",
                    },
                    "name": {
                        "type": "string",
                        "title": "Contact Name",
                        "description": "Full name for the contact.",
                    },
                    "custom_fields": {
                        "type": "array",
                        "title": "Custom Fields",
                        "items": {"type": "object"},
                        "description": "Optional custom fields values.",
                    },
                },
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Create contact",
                    "config": {
                        "subdomain": "mycompany",
                        "name": "John Doe",
                        "custom_fields": [],
                    },
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        subdomain = config.get("subdomain")
        name = config.get("name")
        custom_fields = config.get("custom_fields")

        if not subdomain or not name:
            await logger.error("subdomain and name are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "subdomain and name are required",
                }
            }

        if custom_fields is not None and not isinstance(custom_fields, list):
            await logger.error("custom_fields must be an array when provided")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "custom_fields must be an array",
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="amocrm",
            strategy="oauth",
        )
        if not creds:
            await logger.error("AmoCRM credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "AmoCRM credentials not found",
                }
            }

        payload = creds.get("payload", {}) or creds
        access_token = payload.get("access_token")
        if not access_token:
            await logger.error(f"access_token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "access_token not found in credentials",
                }
            }

        base_domain = subdomain if "." in subdomain else f"{subdomain}.amocrm.ru"
        url = f"https://{base_domain}/api/v4/contacts"

        contact_data: Dict[str, Any] = {"name": str(name)}
        if custom_fields is not None:
            contact_data["custom_fields_values"] = custom_fields

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    json=[contact_data],
                )
        except httpx.RequestError as e:
            await logger.error(f"AmoCRM request failed: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 502,
                    "description": "Failed to reach AmoCRM",
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while calling AmoCRM: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "Unexpected error while calling AmoCRM",
                }
            }

        response_text = response.text
        try:
            response_json = response.json()
        except ValueError:
            response_json = None

        if response.status_code >= 400:
            await logger.error(f"AmoCRM error {response.status_code}: {response_text}")
            return {
                "response": {
                    "ok": False,
                    "error_code": response.status_code,
                    "description": response_text or "AmoCRM error",
                }
            }

        contact = None
        if isinstance(response_json, dict):
            embedded = response_json.get("_embedded", {})
            contacts = embedded.get("contacts")
            if isinstance(contacts, list) and contacts:
                contact = contacts[0]

        result_name = str(name)
        if isinstance(contact, dict):
            response_name = contact.get("name")
            if response_name:
                result_name = response_name

        result = {
            "id": contact.get("id") if isinstance(contact, dict) else None,
            "name": result_name,
        }

        return {
            "response": {
                "ok": True,
                "result": result,
            }
        }
