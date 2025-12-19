"""Vkontakte Wall Get integration (wall.get)."""
from typing import Dict, Any, Optional
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class VkontakteWallGetIntegration(BaseIntegration):
    """Получение записей со стены ВКонтакте через метод wall.get."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vkontakte_wall_get",
            version="1.0.0",
            name="Vkontakte Wall Get",
            description="Получение записей со стены ВКонтакте (wall.get)",
            category="social",
            icon_s3_key="icons/integrations/vkontakte.svg",
            color="#4C75A3",
            config_schema={
                "type": "object",
                "properties": {
                    "owner_id": {"type": "integer", "title": "owner_id"},
                    "domain": {"type": "string", "title": "domain"},
                    "offset": {"type": "integer", "title": "offset"},
                    "count": {"type": "integer", "title": "count", "maximum": 100},
                    "filter": {"type": "string", "title": "filter", "description": "all, owner, others, suggests, postponed"},
                    "extended": {"type": ["integer", "boolean"], "title": "extended"},
                    "fields": {"type": ["string", "array"], "title": "fields"},
                },
                "additionalProperties": True,
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[
                {
                    "title": "Получить последние посты",
                    "config": {"owner_id": 123456, "count": 10, "extended": 1, "fields": "photo_100,online"},
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
        # Resolve credentials (provider 'other' with api_key fallback)
        strategy = self.metadata.credentials_strategy or "oauth"
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy=strategy)
        if not creds:
            creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")

        if not creds:
            await logger.error("VK credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "VK credentials not found"}}

        payload = creds.get("payload") if isinstance(creds, dict) else None
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        access_token = payload.get("access_token") or payload.get("token") or payload.get("accessToken")
        if not access_token:
            await logger.error("VK access_token not provided in credentials payload")
            return {"response": {"ok": False, "error_code": 401, "description": "VK access_token not provided in credentials"}}

        # Build params
        params: Dict[str, Any] = {"access_token": access_token, "v": config.get("v", "5.131")}

        owner_id = config.get("owner_id")
        domain = config.get("domain")
        offset = config.get("offset")
        count = config.get("count")
        filter_val = config.get("filter")
        extended = config.get("extended")
        fields = config.get("fields")

        # Validation
        if owner_id is not None:
            try:
                params["owner_id"] = int(owner_id)
            except Exception:
                await logger.error("owner_id must be integer")
                return {"response": {"ok": False, "error_code": 400, "description": "owner_id must be integer"}}

        if domain is not None:
            params["domain"] = str(domain)

        if offset is not None:
            try:
                params["offset"] = int(offset)
            except Exception:
                await logger.error("offset must be integer")
                return {"response": {"ok": False, "error_code": 400, "description": "offset must be integer"}}

        if count is not None:
            try:
                c = int(count)
                if c > 100:
                    c = 100
                params["count"] = c
            except Exception:
                await logger.error("count must be integer")
                return {"response": {"ok": False, "error_code": 400, "description": "count must be integer"}}

        if filter_val is not None:
            params["filter"] = str(filter_val)

        if extended is not None:
            # accept bool or int
            params["extended"] = 1 if bool(extended) else 0

        if fields is not None:
            if isinstance(fields, (list, tuple)):
                params["fields"] = ",".join(map(str, fields))
            else:
                params["fields"] = str(fields)

        url = "https://api.vk.com/method/wall.get"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                try:
                    resp.raise_for_status()
                except Exception as e:
                    await logger.error(f"HTTP error when calling VK: {e}")
                    code = getattr(resp, "status_code", 500)
                    return {"response": {"ok": False, "error_code": code, "description": str(e)}}

                try:
                    body = resp.json()
                except Exception:
                    return {"response": {"ok": True, "result": resp.text}}

                # VK API error
                if isinstance(body, dict) and "error" in body:
                    err = body.get("error", {})
                    msg = err.get("error_msg") or err.get("error_reason") or str(err)
                    await logger.error(f"VK API error: {msg}")
                    return {"response": {"ok": False, "error_code": 400, "description": msg}}

                return {"response": {"ok": True, "result": body.get("response", body)}}

        except httpx.RequestError as e:
            await logger.error(f"Request error when calling VK: {e}")
            return {"response": {"ok": False, "error_code": 503, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error in VkontakteWallGetIntegration: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
