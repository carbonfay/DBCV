"""Bitrix24: Get Activity integration (crm.activity.get).

Получает CRM-активность Bitrix24 по её ID через webhook или domain+access_token используя httpx.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

import httpx


class Bitrix24GetActivityIntegration(BaseIntegration):
    """Интеграция Bitrix24: получение активности (crm.activity.get)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_get_activity",
            version="1.0.0",
            name="Bitrix24 Get Activity",
            description="Получение CRM-активности из Bitrix24 по ID (crm.activity.get)",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "integer", "title": "ID", "description": "ID активности в Bitrix24"}
                },
                "additionalProperties": False,
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[{"title": "Get activity by ID", "config": {"id": 112233}}],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Выполняет запрос crm.activity.get по ID.

        Поддерживает webhook_url или domain + access_token в credentials payload.
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

        # Validate id
        activity_id = config.get("id")
        try:
            activity_id = int(activity_id)
        except Exception:
            await logger.error("config.id is required and must be an integer")
            return {"response": {"ok": False, "error_code": 400, "description": "config.id is required and must be an integer"}}

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

        params = {"ID": activity_id}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # webhook
                if webhook_url:
                    try:
                        url = webhook_url.rstrip("/") + "/crm.activity.get"
                        resp = await client.post(url, json=params)
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

                        url = f"{base}/rest/crm.activity.get.json"
                        params_q = {"id": activity_id, "auth": access_token}
                        resp = await client.get(url, params=params_q)
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
