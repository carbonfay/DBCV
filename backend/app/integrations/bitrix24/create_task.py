"""Bitrix24: CreateTask integration (tasks.task.add).

Создаёт задачу в Bitrix24 через webhook или domain+access_token используя httpx.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

import httpx


class Bitrix24CreateTaskIntegration(BaseIntegration):
    """Интеграция Bitrix24: создание задачи (tasks.task.add)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_create_task",
            version="1.0.0",
            name="Bitrix24 Create Task",
            description="Создание задачи в Bitrix24 (tasks.task.add)",
            category="tasks",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string", "title": "Title", "description": "Заголовок задачи (TITLE)"},
                    "description": {"type": "string", "title": "Description", "description": "Описание задачи (DESCRIPTION)"},
                    "responsible_id": {"type": "integer", "title": "Responsible ID", "description": "ID ответственного (RESPONSIBLE_ID)"},
                    "deadline": {"type": "string", "format": "date-time", "title": "Deadline", "description": "Срок выполнения (ISO-8601)"},
                    "priority": {"type": "integer", "title": "Priority", "description": "Приоритет задачи"},
                    "custom_fields": {"type": "object", "title": "Custom fields (UF_*)", "description": "Дополнительные пользовательские поля (UF_*)"},
                },
                "additionalProperties": True,
            },
            credentials_provider="other",
            credentials_strategy="oauth",
            examples=[
                {
                    "title": "Создать новую задачу",
                    "config": {"title": "Test task", "description": "Описание задачи", "responsible_id": 1},
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
        """Создаёт задачу через tasks.task.add.

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

        # Build fields object for Bitrix API
        fields: Dict[str, Any] = {}

        # Backwards compatible: accept either `fields` dict or top-level properties
        cfg_fields = config.get("fields")
        if isinstance(cfg_fields, dict) and cfg_fields:
            fields.update(cfg_fields)
        else:
            # map common keys
            if "title" in config and config.get("title") is not None:
                fields["TITLE"] = config.get("title")
            if "description" in config and config.get("description") is not None:
                fields["DESCRIPTION"] = config.get("description")
            if "responsible_id" in config and config.get("responsible_id") is not None:
                fields["RESPONSIBLE_ID"] = config.get("responsible_id")
            if "deadline" in config and config.get("deadline") is not None:
                fields["DEADLINE"] = config.get("deadline")
            if "priority" in config and config.get("priority") is not None:
                fields["PRIORITY"] = config.get("priority")

            # custom_fields is a place for UF_* keys
            custom = config.get("custom_fields")
            if isinstance(custom, dict):
                for ck, cv in custom.items():
                    fields[ck] = cv

            # allow passing UF_* or TAGS/GROUP_ID etc at top-level
            for k, v in config.items():
                if isinstance(k, str) and (k.startswith("UF_") or k.upper() in {"TAGS", "GROUP_ID", "AUDITORS", "ACCOMPLICES"}):
                    fields[k] = v

        if not fields:
            await logger.error("config.title (or fields) is required to create a task")
            return {"response": {"ok": False, "error_code": 400, "description": "config.title (or fields) is required to create a task"}}

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
                # Try webhook first
                if webhook_url:
                    try:
                        url = webhook_url.rstrip("/") + "/tasks.task.add"
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

                        url = f"{base}/rest/tasks.task.add.json"
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
