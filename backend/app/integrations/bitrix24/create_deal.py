"""Bitrix24: CreateDeal integration (crm.deal.add).

Создаёт сделку в Bitrix24 через webhook или domain+access_token используя httpx.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

import httpx


class Bitrix24CreateDealIntegration(BaseIntegration):
    """Интеграция Bitrix24: создание сделки (crm.deal.add)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_create_deal",
            version="1.0.0",
            name="Bitrix24 Create Deal",
            description="Создание сделки в Bitrix24 (crm.deal.add)",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                "properties": {
                    # Expose common deal fields as top-level properties so frontend renders them as separate inputs
                    "TITLE": {"type": "string", "title": "TITLE", "description": "Deal title. If empty, generated as Deal #{id}."},
                    "OPPORTUNITY": {"type": "number", "title": "OPPORTUNITY", "description": "Amount (default 0.00)."},
                    "CURRENCY_ID": {"type": "string", "title": "CURRENCY_ID", "description": "Currency identifier (crm_currency)."},
                    "TYPE_ID": {"type": "string", "title": "TYPE_ID", "description": "String identifier of the deal type (crm_status)."},
                    "CATEGORY_ID": {"type": "integer", "title": "CATEGORY_ID", "description": "Identifier of the funnel (>=0)."},
                    "STAGE_ID": {"type": "string", "title": "STAGE_ID", "description": "Stage of the deal (crm_status)."},
                    "PROBABILITY": {"type": "integer", "title": "PROBABILITY", "description": "Probability in percent."},
                    "IS_RECURRING": {"type": "string", "title": "IS_RECURRING", "description": "Is the deal a template for recurring deals. Y/N."},
                    "IS_RETURN_CUSTOMER": {"type": "string", "title": "IS_RETURN_CUSTOMER", "description": "Is the deal a repeat. Y/N."},
                    "IS_REPEATED_APPROACH": {"type": "string", "title": "IS_REPEATED_APPROACH", "description": "Is repeated approach. Y/N."},
                    "IS_MANUAL_OPPORTUNITY": {"type": "string", "title": "IS_MANUAL_OPPORTUNITY", "description": "Is manual calculation enabled. Y/N."},
                    "TAX_VALUE": {"type": "number", "title": "TAX_VALUE", "description": "Tax amount."},
                    "COMPANY_ID": {"type": "integer", "title": "COMPANY_ID", "description": "Identifier of the company associated with the deal."},
                    "CONTACT_ID": {"type": "integer", "title": "CONTACT_ID", "description": "Contact (deprecated)."},
                    "CONTACT_IDS": {"type": "array", "items": {"type": "integer"}, "title": "CONTACT_IDS", "description": "List of contacts associated with the deal."},
                    "BEGINDATE": {"type": "string", "format": "date", "title": "BEGINDATE", "description": "Start date."},
                    "CLOSEDATE": {"type": "string", "format": "date", "title": "CLOSEDATE", "description": "Completion date."},
                    "OPENED": {"type": "string", "title": "OPENED", "description": "Is the deal available to everyone. Y/N."},
                    "CLOSED": {"type": "string", "title": "CLOSED", "description": "Is the deal closed. Y/N."},
                    "COMMENTS": {"type": "string", "title": "COMMENTS", "description": "Comment (supports bb-codes)."},
                    "ASSIGNED_BY_ID": {"type": "integer", "title": "ASSIGNED_BY_ID", "description": "Responsible user id."},
                    "SOURCE_ID": {"type": "string", "title": "SOURCE_ID", "description": "String identifier of the source type."},
                    "SOURCE_DESCRIPTION": {"type": "string", "title": "SOURCE_DESCRIPTION", "description": "Additional info about the source."},
                    "ADDITIONAL_INFO": {"type": "string", "title": "ADDITIONAL_INFO", "description": "Additional information."},
                    "LOCATION_ID": {"type": "string", "title": "LOCATION_ID", "description": "Client location (system field)."},
                    "ORIGINATOR_ID": {"type": "string", "title": "ORIGINATOR_ID", "description": "Identifier of the data source."},
                    "ORIGIN_ID": {"type": "string", "title": "ORIGIN_ID", "description": "Identifier of the element in the data source."},
                    "UTM_SOURCE": {"type": "string", "title": "UTM_SOURCE", "description": "Advertising system."},
                    "UTM_MEDIUM": {"type": "string", "title": "UTM_MEDIUM", "description": "Type of traffic (CPC, CPM, etc.)."},
                    "UTM_CAMPAIGN": {"type": "string", "title": "UTM_CAMPAIGN", "description": "Advertising campaign name."},
                    "UTM_CONTENT": {"type": "string", "title": "UTM_CONTENT", "description": "Content of campaign."},
                    "UTM_TERM": {"type": "string", "title": "UTM_TERM", "description": "Search term of campaign."},
                    "TRACE": {"type": "string", "title": "TRACE", "description": "Information for Sales Intelligence."},
                    # relationship fields and custom fields
                    "PARENT_ID_*": {"type": "string", "title": "PARENT_ID_*", "description": "Relationship fields, use PARENT_ID_{entityId} for SPA relationships."},
                    "custom_fields": {"type": "object", "title": "Custom fields (UF_CRM_...)", "description": "Use for UF_CRM_* custom fields and any additional mapping."},
                    # keep params as separate group too (optional)
                    "params": {
                        "type": "object",
                        "title": "Params",
                        "description": "Additional method parameters (if needed).",
                        "properties": {
                            "OPENED": {"type": "string", "title": "OPENED", "description": "Is the deal available to everyone. Y/N."},
                            "CLOSED": {"type": "string", "title": "CLOSED", "description": "Is the deal closed. Y/N."},
                            "BEGINDATE": {"type": "string", "format": "date", "title": "BEGINDATE", "description": "Start date."},
                            "CLOSEDATE": {"type": "string", "format": "date", "title": "CLOSEDATE", "description": "Completion date."}
                        },
                        "additionalProperties": True
                    }
                },
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[
                {
                    "title": "Create deal with title, opportunity and currency",
                    "config": {"TITLE": "New deal", "OPPORTUNITY": 1000, "CURRENCY_ID": "USD"},
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
        """Создаёт сделку через crm.deal.add.

        Поддерживает webhook_url или domain+access_token в credentials payload.
        """
        strategy = self.metadata.credentials_strategy or "oauth"
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy=strategy)
        if not creds:
            creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")

        if not creds:
            await logger.error("Bitrix24 credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Bitrix24 credentials not found"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds

        # Backwards-compatible: accept either `fields` object or individual top-level properties
        params = config.get("params")

        fields: Dict[str, Any] = {}

        # If the older `fields` object is provided, use it directly
        cfg_fields = config.get("fields")
        if isinstance(cfg_fields, dict) and cfg_fields:
            fields.update(cfg_fields)
        else:
            # Collect common top-level properties into fields
            top_keys = [
                "TITLE",
                "OPPORTUNITY",
                "CURRENCY_ID",
                "TYPE_ID",
                "CATEGORY_ID",
                "STAGE_ID",
                "PROBABILITY",
                "IS_RECURRING",
                "IS_RETURN_CUSTOMER",
                "IS_REPEATED_APPROACH",
                "IS_MANUAL_OPPORTUNITY",
                "TAX_VALUE",
                "COMPANY_ID",
                "CONTACT_ID",
                "CONTACT_IDS",
                "BEGINDATE",
                "CLOSEDATE",
                "OPENED",
                "CLOSED",
                "COMMENTS",
                "ASSIGNED_BY_ID",
                "SOURCE_ID",
                "SOURCE_DESCRIPTION",
                "ADDITIONAL_INFO",
                "LOCATION_ID",
                "ORIGINATOR_ID",
                "ORIGIN_ID",
                "UTM_SOURCE",
                "UTM_MEDIUM",
                "UTM_CAMPAIGN",
                "UTM_CONTENT",
                "UTM_TERM",
                "TRACE",
            ]

            for k in top_keys:
                if k in config and config[k] is not None:
                    fields[k] = config[k]

            # merge custom_fields (UF_CRM_*) if provided
            custom = config.get("custom_fields")
            if isinstance(custom, dict):
                for ck, cv in custom.items():
                    fields[ck] = cv

            # also include any keys that look like UF_CRM_* or PARENT_ID_*
            for k, v in config.items():
                if isinstance(k, str) and (k.startswith("UF_CRM_") or k.startswith("PARENT_ID_")):
                    fields[k] = v

        # If after all that we still have no fields, it's an error
        if not fields:
            await logger.error("config must contain either `fields` object or at least one deal field property (TITLE, OPPORTUNITY, etc.)")
            return {"response": {"ok": False, "error_code": 400, "description": "config.fields is required and must be an object or provide top-level deal properties like TITLE, OPPORTUNITY, etc."}}

        request_data: Dict[str, Any] = {"fields": fields}
        if params and isinstance(params, dict):
            request_data["params"] = params

        webhook_url = payload.get("webhook_url") or payload.get("webhook")
        domain = payload.get("domain") or payload.get("base_url") or payload.get("url")
        access_token = payload.get("access_token") or payload.get("token") or payload.get("accessToken")

        async def _handle_response(resp: httpx.Response) -> Dict[str, Any]:
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
                        url = webhook_url.rstrip("/") + "/crm.deal.add"
                        resp = await client.post(url, json=request_data)
                        handled = await _handle_response(resp)
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

                        url = f"{base}/rest/crm.deal.add.json"
                        params_q = {"auth": access_token}
                        resp = await client.post(url, params=params_q, json=request_data)
                        handled = await _handle_response(resp)
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
