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
                    # Основные поля сделки — отображаются как отдельные поля в UI
                    "TITLE": {"type": "string", "title": "Название сделки", "description": "Название сделки. Если пусто — будет сгенерировано автоматически."},
                    "OPPORTUNITY": {"type": "number", "title": "Сумма", "description": "Сумма сделки (по умолчанию 0.00)."},
                    "CURRENCY_ID": {"type": "string", "title": "Валюта", "description": "Код валюты (например: USD)."},
                    "TYPE_ID": {"type": "string", "title": "Тип сделки", "description": "Строковый идентификатор типа сделки."},
                    "CATEGORY_ID": {"type": "integer", "title": "Воронка (CATEGORY_ID)", "description": "ID воронки/категории (целое число)."},
                    "STAGE_ID": {"type": "string", "title": "Стадия (STAGE_ID)", "description": "Код стадии сделки в воронке."},
                    "PROBABILITY": {"type": "integer", "title": "Вероятность", "description": "Вероятность успеха в процентах."},
                    "IS_RECURRING": {"type": "string", "title": "Повторяющаяся", "description": "Является ли шаблоном для повторяющихся сделок (Y/N)."},
                    "IS_RETURN_CUSTOMER": {"type": "string", "title": "Повторный клиент", "description": "Отмечает, что клиент возвращается (Y/N)."},
                    "IS_REPEATED_APPROACH": {"type": "string", "title": "Повторный подход", "description": "Повторный подход к клиенту (Y/N)."},
                    "IS_MANUAL_OPPORTUNITY": {"type": "string", "title": "Ручной расчёт суммы", "description": "Ручной ввод суммы вместо автоматического расчёта (Y/N)."},
                    "TAX_VALUE": {"type": "number", "title": "Налог", "description": "Сумма налога для сделки."},
                    "COMPANY_ID": {"type": "integer", "title": "Компания (ID)", "description": "ID компании, связанной со сделкой."},
                    "CONTACT_ID": {"type": "integer", "title": "Контакт (ID)", "description": "ID основного контакта (устаревшее поле)."},
                    "CONTACT_IDS": {"type": "array", "items": {"type": "integer"}, "title": "Контакты (IDs)", "description": "Список ID контактов, связанных со сделкой."},
                    "BEGINDATE": {"type": "string", "format": "date", "title": "Дата начала", "description": "Дата начала сделки (YYYY-MM-DD)."},
                    "CLOSEDATE": {"type": "string", "format": "date", "title": "Дата закрытия", "description": "Ожидаемая дата закрытия сделки (YYYY-MM-DD)."},
                    "OPENED": {"type": "string", "title": "Доступна всем", "description": "Доступна ли сделка всем пользователям (Y/N)."},
                    "CLOSED": {"type": "string", "title": "Закрыта", "description": "Пометка о закрытии сделки (Y/N)."},
                    "COMMENTS": {"type": "string", "title": "Комментарий", "description": "Комментарий к сделке (поддерживаются bb-коды)."},
                    "ASSIGNED_BY_ID": {"type": "integer", "title": "Ответственный (ID)", "description": "ID пользователя, ответственного за сделку."},
                    "SOURCE_ID": {"type": "string", "title": "Источник", "description": "Строковый идентификатор источника сделки."},
                    "SOURCE_DESCRIPTION": {"type": "string", "title": "Описание источника", "description": "Дополнительная информация об источнике поступления сделки."},
                    "ADDITIONAL_INFO": {"type": "string", "title": "Дополнительно", "description": "Дополнительная информация о сделке."},
                    "LOCATION_ID": {"type": "string", "title": "Локация", "description": "Местоположение клиента (системное поле)."},
                    "ORIGINATOR_ID": {"type": "string", "title": "Источник данных (ID)", "description": "Идентификатор источника данных (originator)."},
                    "ORIGIN_ID": {"type": "string", "title": "ID во внешней системе", "description": "Идентификатор записи во внешней системе."},
                    "UTM_SOURCE": {"type": "string", "title": "UTM: Источник", "description": "Источник трафика для аналитики (utm_source)."},
                    "UTM_MEDIUM": {"type": "string", "title": "UTM: Канал", "description": "Тип трафика (CPC, CPM и т.д.)."},
                    "UTM_CAMPAIGN": {"type": "string", "title": "UTM: Кампания", "description": "Название рекламной кампании (utm_campaign)."},
                    "UTM_CONTENT": {"type": "string", "title": "UTM: Контент", "description": "Контент кампании (utm_content)."},
                    "UTM_TERM": {"type": "string", "title": "UTM: Поиск", "description": "Ключевое слово кампании (utm_term)."},
                    "TRACE": {"type": "string", "title": "Trace / Аналитика", "description": "Информация для аналитики или sales intelligence."},
                    # relationship fields and custom fields
                    "PARENT_ID_*": {"type": "string", "title": "Связи (PARENT_ID_*)", "description": "Поля связей: используйте PARENT_ID_{entityId} для связей между сущностями."},
                    "custom_fields": {"type": "object", "title": "Пользовательские поля (UF_CRM_...)", "description": "Используйте для кастомных полей UF_CRM_* и дополнительного маппинга."},
                    # keep params as separate group too (optional)
                    "params": {
                        "type": "object",
                        "title": "Параметры",
                        "description": "Дополнительные параметры метода (необязательно).",
                        "properties": {
                            "OPENED": {"type": "string", "title": "Доступна всем", "description": "Доступна ли сделка всем (Y/N)."},
                            "CLOSED": {"type": "string", "title": "Закрыта", "description": "Пометка о закрытии сделки (Y/N)."},
                            "BEGINDATE": {"type": "string", "format": "date", "title": "Дата начала", "description": "Дата начала (YYYY-MM-DD)."},
                            "CLOSEDATE": {"type": "string", "format": "date", "title": "Дата закрытия", "description": "Дата закрытия (YYYY-MM-DD)."}
                        },
                        "additionalProperties": True
                    }
                },
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[
                {
                    "title": "Создать сделку: название, сумма и валюта",
                    "config": {"TITLE": "Новая сделка", "OPPORTUNITY": 1000, "CURRENCY_ID": "USD"},
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

        # Variables support for playback: accept `variables` or `context` in config
        vars_input = config.get("variables") or config.get("context") or {}
        if isinstance(vars_input, str):
            try:
                import json as _json

                vars_input = _json.loads(vars_input)
            except Exception:
                vars_input = {}
        variables = vars_input if isinstance(vars_input, dict) else {}

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
                        # publish last_request with variables for playback/debugging
                        await logger.send_variables({"bot.last_request": {"url": url, "params": None, "data": request_data, "variables": variables}})
                        await logger.info(f"bot.last_request: {request_data}")
                        resp = await client.post(url, json=request_data)
                        handled = await _handle_response(resp)
                        # publish response including variables
                        await logger.send_variables({"bot.last_response": {"ok": handled.get("ok"), "result": handled.get("result"), "error": handled.get("error"), "variables": variables}})
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
                        # publish last_request with variables for playback/debugging
                        await logger.send_variables({"bot.last_request": {"url": url, "params": params_q, "data": request_data, "variables": variables}})
                        await logger.info(f"bot.last_request: {request_data}")
                        resp = await client.post(url, params=params_q, json=request_data)
                        handled = await _handle_response(resp)
                        # publish response including variables
                        await logger.send_variables({"bot.last_response": {"ok": handled.get("ok"), "result": handled.get("result"), "error": handled.get("error"), "variables": variables}})
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
