"""Bitrix24: CreateCompany integration (crm.company.add).

Создаёт компанию в Bitrix24 через webhook или domain+access_token используя httpx.
"""
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

import httpx


class Bitrix24CreateCompanyIntegration(BaseIntegration):
    """Интеграция Bitrix24: создание компании (crm.company.add)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_create_company",
            version="1.0.0",
            name="Bitrix24 Create Company",
            description="Создание компании в Bitrix24 (crm.company.add)",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string", "title": "Title", "description": "Название компании (TITLE)"},
                    "company_type": {"type": "string", "title": "Company type", "description": "Тип компании (COMPANY_TYPE)"},
                    "industry": {"type": "string", "title": "Industry", "description": "Отрасль (INDUSTRY)"},
                    "phones": {"type": "array", "items": {"type": "object"}, "title": "Phones", "description": "Список телефонов (PHONE)"},
                    "emails": {"type": "array", "items": {"type": "object"}, "title": "Emails", "description": "Список email (EMAIL)"},
                    "websites": {"type": "array", "items": {"type": "object"}, "title": "Websites", "description": "Сайты компании (WEB)"},
                },
                "additionalProperties": True,
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[
                {
                    "title": "Создать компанию",
                    "config": {
                        "title": "ООО Ромашка",
                        "company_type": "CUSTOMER",
                        "industry": "IT",
                        "phones": [{"VALUE": "+7 (495) 111-22-33", "VALUE_TYPE": "WORK"}],
                        "emails": [{"VALUE": "info@romashka.ru", "VALUE_TYPE": "WORK"}],
                        "websites": [{"VALUE": "https://romashka.ru", "VALUE_TYPE": "WORK"}],
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
        """Создаёт компанию через crm.company.add.

        Поддерживает webhook_url или domain + access_token.
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

        # Required: title
        title = config.get("title")
        if not title:
            await logger.error("config.title (company title) is required")
            return {"response": {"ok": False, "error_code": 400, "description": "config.title (company title) is required"}}

        fields: Dict[str, Any] = {}
        fields["TITLE"] = title

        company_type = config.get("company_type")
        if company_type is not None:
            fields["COMPANY_TYPE"] = company_type

        industry = config.get("industry")
        if industry is not None:
            fields["INDUSTRY"] = industry

        phones = config.get("phones")
        if isinstance(phones, list) and phones:
            fields["PHONE"] = phones

        emails = config.get("emails")
        if isinstance(emails, list) and emails:
            fields["EMAIL"] = emails

        websites = config.get("websites")
        if isinstance(websites, list) and websites:
            fields["WEB"] = websites

        # allow UF_* custom fields
        for k, v in config.items():
            if isinstance(k, str) and k.startswith("UF_"):
                fields[k] = v

        request_data = {"fields": fields}

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
                        url = webhook_url.rstrip("/") + "/crm.company.add"
                        resp = await client.post(url, json=request_data)
                        handled = await _handle_bitrix_response(resp)
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

                        url = f"{base}/rest/crm.company.add.json"
                        params_q = {"auth": access_token}
                        resp = await client.post(url, params=params_q, json=request_data)
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

        await logger.error("Unable to call Bitrix24: no working endpoint or token")
        return {"response": {"ok": False, "error_code": 500, "description": "Unable to call Bitrix24: no working endpoint or token"}}
