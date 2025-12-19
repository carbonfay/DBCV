"""Bitrix24 Update Deal integration (crm.deal.update)."""
from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class Bitrix24UpdateDealIntegration(BaseIntegration):
    """Обновление сделки в Bitrix24 через crm.deal.update."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_update_deal",
            version="1.0.0",
            name="Bitrix24 Update Deal",
            description="Обновление сделки в Bitrix24 (crm.deal.update)",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "integer", "title": "Deal ID", "description": "ID сделки в Bitrix24"},
                    "TITLE": {"type": "string", "title": "TITLE", "description": "Title of the deal"},
                    "TYPE_ID": {"type": "string", "title": "TYPE_ID", "description": "String identifier of the deal type (crm_status)"},
                    "STAGE_ID": {"type": "string", "title": "STAGE_ID", "description": "Stage of the deal (crm_status)"},
                    "IS_RECURRING": {"type": "string", "title": "IS_RECURRING", "description": "Is the deal a template for a recurring deal? (Y/N)"},
                    "IS_RETURN_CUSTOMER": {"type": "string", "title": "IS_RETURN_CUSTOMER", "description": "Is the deal a repeat? (Y/N)"},
                    "IS_REPEATED_APPROACH": {"type": "string", "title": "IS_REPEATED_APPROACH", "description": "Is the deal a repeated approach? (Y/N)"},
                    "PROBABILITY": {"type": "integer", "title": "PROBABILITY", "description": "Probability, %"},
                    "CURRENCY_ID": {"type": "string", "title": "CURRENCY_ID", "description": "Currency (crm_currency)"},
                    "OPPORTUNITY": {"type": "number", "title": "OPPORTUNITY", "description": "Amount (double)"},
                    "IS_MANUAL_OPPORTUNITY": {"type": "string", "title": "IS_MANUAL_OPPORTUNITY", "description": "Is manual calculation mode enabled? (Y/N)"},
                    "TAX_VALUE": {"type": "number", "title": "TAX_VALUE", "description": "Tax amount"},
                    "COMPANY_ID": {"type": "integer", "title": "COMPANY_ID", "description": "Identifier of the company associated with the deal (crm_company)"},
                    "CONTACT_ID": {"type": "integer", "title": "CONTACT_ID", "description": "Contact (deprecated)"},
                    "CONTACT_IDS": {"type": "array", "items": {"type": "integer"}, "title": "CONTACT_IDS", "description": "List of contacts associated with the deal"},
                    "BEGINDATE": {"type": "string", "format": "date", "title": "BEGINDATE", "description": "Start date"},
                    "CLOSEDATE": {"type": "string", "format": "date", "title": "CLOSEDATE", "description": "End date"},
                    "OPENED": {"type": "string", "title": "OPENED", "description": "Is the deal available to everyone? (Y/N)"},
                    "CLOSED": {"type": "string", "title": "CLOSED", "description": "Is the deal closed? (Y/N)"},
                    "COMMENTS": {"type": "string", "title": "COMMENTS", "description": "Comment. Supports bb-codes"},
                    "ASSIGNED_BY_ID": {"type": "integer", "title": "ASSIGNED_BY_ID", "description": "Responsible person (user)"},
                    "SOURCE_ID": {"type": "string", "title": "SOURCE_ID", "description": "String identifier of the source type (crm_status)"},
                    "SOURCE_DESCRIPTION": {"type": "string", "title": "SOURCE_DESCRIPTION", "description": "Additional information about the source"},
                    "ADDITIONAL_INFO": {"type": "string", "title": "ADDITIONAL_INFO", "description": "Additional information"},
                    "LOCATION_ID": {"type": "string", "title": "LOCATION_ID", "description": "Client's location (system field)"},
                    "ORIGINATOR_ID": {"type": "string", "title": "ORIGINATOR_ID", "description": "Identifier of the data source"},
                    "ORIGIN_ID": {"type": "string", "title": "ORIGIN_ID", "description": "Identifier of the element in the data source"},
                    "UTM_SOURCE": {"type": "string", "title": "UTM_SOURCE", "description": "Advertising system"},
                    "UTM_MEDIUM": {"type": "string", "title": "UTM_MEDIUM", "description": "Type of traffic"},
                    "UTM_CAMPAIGN": {"type": "string", "title": "UTM_CAMPAIGN", "description": "Identifier of the advertising campaign"},
                    "UTM_CONTENT": {"type": "string", "title": "UTM_CONTENT", "description": "Content of the campaign"},
                    "UTM_TERM": {"type": "string", "title": "UTM_TERM", "description": "Search condition of the campaign"},
                    "fields": {"type": "object", "title": "Fields", "description": "Legacy fields object (alternative to top-level properties)"},
                },
                "patternProperties": {
                    "^UF_CRM_": {"type": ["string", "number", "array", "object"], "title": "Custom Field", "description": "Custom UF_CRM_* fields"},
                    "^PARENT_ID_": {"type": ["integer", "string"], "title": "Parent Relation", "description": "PARENT_ID_* relationship fields"}
                },
                "additionalProperties": True
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[
                {
                    "title": "Обновить сделку",
                    "config": {
                        "id": 789,
                        "fields": {
                            "TITLE": "Изменённое название",
                            "OPPORTUNITY": 120000,
                            "STAGE_ID": "PROPOSAL"
                        }
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        # Получаем credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="oauth",
        )

        if not creds:
            await logger.error("Bitrix24 credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Bitrix24 credentials not found"
                }
            }

        payload = creds.get("payload") if isinstance(creds, dict) else None
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        webhook = payload.get("webhook_url") or payload.get("webhook")
        domain = payload.get("domain") or payload.get("base_url") or payload.get("url")
        token = payload.get("access_token") or payload.get("token")

        # Валидация параметров
        deal_id = config.get("id")
        # fields может быть передан либо как объект config['fields'], либо как набор топ-левел полей
        fields = config.get("fields") if isinstance(config.get("fields"), dict) else {}

        if not deal_id or not isinstance(deal_id, int):
            await logger.error("id is required and must be an integer")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "id is required and must be an integer"
                }
            }

        # Поддержка удобного ввода: если пользователю в UI задали отдельные поля (TITLE, OPPORTUNITY и т.д.),
        # то они будут переданы как топ-левел свойства. Объединяем их в итоговый fields.
        known_field_names = [
            "TITLE",
            "TYPE_ID",
            "STAGE_ID",
            "IS_RECURRING",
            "IS_RETURN_CUSTOMER",
            "IS_REPEATED_APPROACH",
            "PROBABILITY",
            "CURRENCY_ID",
            "OPPORTUNITY",
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
        ]

        for fname in known_field_names:
            if fname in config and config.get(fname) is not None:
                fields[fname] = config.get(fname)

        # Поддержка кастомных UF_CRM_* и PARENT_ID_* полей — копируем всё, что подходит по префиксу
        for key, val in config.items():
            if isinstance(key, str) and (key.startswith("UF_CRM_") or key.startswith("PARENT_ID_")):
                fields[key] = val

        if not fields or not isinstance(fields, dict):
            await logger.error("fields is required and must be an object (or provide at least one top-level field)")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "fields is required and must be an object (or provide at least one top-level field)"
                }
            }

        # Формируем запрос
        try:
            if webhook:
                url = webhook.rstrip("/") + "/crm.deal.update"
                payload_body = {"id": deal_id, "fields": fields}
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload_body)

            elif domain and token:
                domain_url = domain.rstrip("/")
                if not domain_url.startswith("http"):
                    domain_url = "https://" + domain_url
                url = f"{domain_url}/rest/crm.deal.update.json?auth={token}"
                payload_body = {"id": deal_id, "fields": fields}
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload_body)

            else:
                await logger.error("Bitrix24 webhook or domain/token not provided in credentials")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "Bitrix24 credentials must include webhook_url or domain+access_token"
                    }
                }

            # Проверяем HTTP статус
            try:
                resp.raise_for_status()
            except Exception as e:
                await logger.error(f"HTTP error when calling Bitrix24: {e}")
                code = getattr(resp, "status_code", 500)
                return {
                    "response": {
                        "ok": False,
                        "error_code": code,
                        "description": str(e)
                    }
                }

            body = resp.json() if hasattr(resp, "json") else {}

            # Bitrix API error
            if isinstance(body, dict) and ("error" in body or "error_description" in body):
                err = body.get("error_description") or body.get("error") or "Bitrix24 API error"
                await logger.error(f"Bitrix24 API error: {err}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": err
                    }
                }

            # Успешный ответ
            return {"response": {"ok": True, "result": body}}

        except httpx.RequestError as e:
            await logger.error(f"Request error when calling Bitrix24: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 503,
                    "description": str(e)
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error in Bitrix24UpdateDealIntegration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
