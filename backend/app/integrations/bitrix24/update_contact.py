"""Bitrix24: UpdateContact integration (crm.contact.update).

Редактирует контакт в Bitrix24 через webhook или domain+access_token используя httpx.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

import httpx


class Bitrix24UpdateContactIntegration(BaseIntegration):
    """Интеграция Bitrix24: обновление контакта (crm.contact.update)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_update_contact",
            version="1.0.0",
            name="Bitrix24 Update Contact",
            description="Создание контакта в Bitrix24 (crm.contact.update)",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                # Для обновления требуется id контакта и имя (по требованиям)
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "integer", "title": "Contact ID"},
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
                    "title": "Update contact name, phone and email",
                    "config": {"id": 123, "name": "Ivan Updated", "phone": "+7 999 111-22-33", "email": "ivan.upd@example.com"},
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
        """Выполнить crm.contact.update через webhook или domain+access_token."""
        # Получаем credentials
        strategy = self.metadata.credentials_strategy or "oauth"
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, provider="other", strategy=strategy
        )

        if not creds:
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id, provider="other", strategy="api_key"
            )

        if not creds:
            await logger.error("Bitrix24 credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Bitrix24 credentials not found"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds

        contact_id = config.get("id")
        if contact_id is None:
            await logger.error("config.id (contact id) is required")
            return {"response": {"ok": False, "error_code": 400, "description": "config.id (contact id) is required"}}

        name = config.get("name")
        if not name:
            await logger.error("config.name (contact name) is required")
            return {"response": {"ok": False, "error_code": 400, "description": "config.name (contact name) is required"}}

        # Build fields
        fields: Dict[str, Any] = {}
        fields["NAME"] = name
        last_name = config.get("last_name")
        if last_name:
            fields["LAST_NAME"] = last_name

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

        request_data = {"id": int(contact_id), "fields": fields}

        # Endpoint discovery
        webhook_url = payload.get("webhook_url") or payload.get("webhook")
        domain = payload.get("domain") or payload.get("base_url") or payload.get("url")
        access_token = payload.get("access_token") or payload.get("token") or payload.get("accessToken")

        async def _handle(resp: httpx.Response) -> Dict[str, Any]:
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                await logger.error(f"HTTP error while calling Bitrix24: {e}")
                return {"ok": False, "error": str(e), "status_code": resp.status_code}

            try:
                data = resp.json()
            except Exception:
                return {"ok": True, "result": resp.text}

            if isinstance(data, dict) and ("error" in data and data.get("error")):
                err = data.get("error_description") or data.get("error")
                await logger.error(f"Bitrix24 API error: {err}")
                return {"ok": False, "error": err}

            return {"ok": True, "result": data}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # webhook
                if webhook_url:
                    try:
                        url = webhook_url.rstrip("/") + "/crm.contact.update"
                        resp = await client.post(url, json=request_data)
                        handled = await _handle(resp)
                        if handled.get("ok"):
                            return {"response": {"ok": True, "result": handled.get("result")}}
                        else:
                            return {"response": {"ok": False, "error_code": 400, "description": handled.get("error")}}
                    except Exception as e:
                        await logger.error(f"Bitrix24 webhook request failed: {e}")

                # domain + token
                if domain and access_token:
                    try:
                        base = domain.rstrip("/")
                        if not base.startswith("http"):
                            base = "https://" + base

                        url = f"{base}/rest/crm.contact.update.json"
                        params = {"auth": access_token}
                        resp = await client.post(url, params=params, json=request_data)
                        handled = await _handle(resp)
                        if handled.get("ok"):
                            return {"response": {"ok": True, "result": handled.get("result")}}
                        else:
                            return {"response": {"ok": False, "error_code": 400, "description": handled.get("error")}}
                    except Exception as e:
                        await logger.error(f"Bitrix24 domain/token request failed: {e}")

        except Exception as e:
            await logger.error(f"Unexpected Bitrix24 integration error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}

        await logger.error("Unable to call Bitrix24: no working endpoint or token")
        return {"response": {"ok": False, "error_code": 500, "description": "Unable to call Bitrix24: no working endpoint or token"}}
