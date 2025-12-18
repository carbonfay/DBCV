"""Bitrix24: CreateContact integration (crm.contact.add).

Создаёт контакт в Bitrix24 через webhook или domain+access_token используя httpx.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

import httpx


class Bitrix24CreateContactIntegration(BaseIntegration):
    """Интеграция Bitrix24: создание контакта (crm.contact.add)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_create_contact",
            version="1.0.0",
            name="Bitrix24 Create Contact",
            description="Создание контакта в Bitrix24 (crm.contact.add)",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "title": "Name"},
                    "last_name": {"type": "string", "title": "Last name"},
                    "phone": {"type": "string", "title": "Phone"},
                    "email": {"type": "string", "title": "Email"},
                    "company_id": {"type": "integer", "title": "Company ID"},
                    "assigned_by_id": {"type": "integer", "title": "Assigned by ID"},
                    "source_id": {"type": "string", "title": "Source ID"},
                    "comments": {"type": "string", "title": "Comments"},
                },
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[
                {
                    "title": "Create contact with name, phone and email",
                    "config": {"name": "Ivan", "phone": "+7 999 000-00-00", "email": "ivan@example.com"},
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
        """Создаёт контакт в Bitrix24.

        Поддерживаются два режима авторизации:
        - webhook_url (в payload: webhook_url или webhook)
        - domain + access_token (в payload: domain и access_token)
        """
        # Получаем credentials
        strategy = self.metadata.credentials_strategy or "oauth"
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="other", strategy=strategy
        )

        if not creds:
            # fallback
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id, provider="other", strategy="api_key"
            )

        if not creds:
            await logger.error("Bitrix24 credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Bitrix24 credentials not found"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds

        # Required config: name
        name = config.get("name")
        if not name:
            await logger.error("config.name (contact name) is required")
            return {"response": {"ok": False, "error_code": 400, "description": "config.name (contact name) is required"}}

        # Build fields according to Bitrix API
        fields: Dict[str, Any] = {}
        # Name/Last name
        fields["NAME"] = name
        last_name = config.get("last_name")
        if last_name:
            fields["LAST_NAME"] = last_name

        # Phone and Email should be arrays of dicts
        phone = config.get("phone")
        if phone:
            fields["PHONE"] = [{"VALUE": str(phone), "VALUE_TYPE": "WORK"}]

        email = config.get("email")
        if email:
            fields["EMAIL"] = [{"VALUE": str(email), "VALUE_TYPE": "WORK"}]

        company_id = config.get("company_id")
        if company_id is not None:
            try:
                fields["COMPANY_ID"] = int(company_id)
            except Exception:
                fields["COMPANY_ID"] = company_id

        assigned_by_id = config.get("assigned_by_id")
        if assigned_by_id is not None:
            try:
                fields["ASSIGNED_BY_ID"] = int(assigned_by_id)
            except Exception:
                fields["ASSIGNED_BY_ID"] = assigned_by_id

        source_id = config.get("source_id")
        if source_id:
            fields["SOURCE_ID"] = source_id

        comments = config.get("comments")
        if comments:
            fields["COMMENTS"] = comments

        request_data = {"fields": fields}

        # Endpoint discovery
        webhook_url = payload.get("webhook_url") or payload.get("webhook")
        domain = payload.get("domain") or payload.get("base_url") or payload.get("url")
        access_token = payload.get("access_token") or payload.get("token") or payload.get("accessToken")

        async def _handle_bitrix_response(resp: httpx.Response) -> Dict[str, Any]:
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                await logger.error(f"HTTP error while calling Bitrix24: {e}")
                return {"ok": False, "error": str(e), "status_code": resp.status_code}

            try:
                data = resp.json()
            except Exception:
                # Not JSON
                text = resp.text
                return {"ok": True, "result": text}

            # Bitrix API may return 'error' and 'error_description'
            if isinstance(data, dict) and ("error" in data and data.get("error")):
                err = data.get("error_description") or data.get("error")
                await logger.error(f"Bitrix24 API error: {err}")
                return {"ok": False, "error": err}

            return {"ok": True, "result": data}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Try webhook first
                if webhook_url:
                    try:
                        url = webhook_url.rstrip("/") + "/crm.contact.add"
                        resp = await client.post(url, json=request_data)
                        handled = await _handle_bitrix_response(resp)
                        if handled.get("ok"):
                            return {"response": {"ok": True, "result": handled.get("result")}}
                        else:
                            return {"response": {"ok": False, "error_code": 400, "description": handled.get("error")}}
                    except Exception as e:
                        await logger.error(f"Bitrix24 webhook request failed: {e}")

                # Then try domain + token
                if domain and access_token:
                    try:
                        base = domain.rstrip("/")
                        if not base.startswith("http"):
                            base = "https://" + base

                        # Prefer POST to .json endpoint with auth param
                        url = f"{base}/rest/crm.contact.add.json"
                        params = {"auth": access_token}
                        resp = await client.post(url, params=params, json=request_data)
                        handled = await _handle_bitrix_response(resp)
                        if handled.get("ok"):
                            return {"response": {"ok": True, "result": handled.get("result")}}
                        else:
                            return {"response": {"ok": False, "error_code": 400, "description": handled.get("error")}}
                    except Exception as e:
                        await logger.error(f"Bitrix24 domain/token request failed: {e}")

        except Exception as e:
            await logger.error(f"Unexpected Bitrix24 integration error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}

        # If neither method worked
        await logger.error("Unable to call Bitrix24: no working endpoint or token")
        return {"response": {"ok": False, "error_code": 500, "description": "Unable to call Bitrix24: no working endpoint or token"}}
