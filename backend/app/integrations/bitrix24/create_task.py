"""Bitrix24 Create Task integration (tasks.task.add)."""
from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class Bitrix24CreateTaskIntegration(BaseIntegration):
    """Создание задачи в Bitrix24 через tasks.task.add."""

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
                    "title": {"type": "string", "title": "Title", "description": "Заголовок задачи"},
                    "description": {"type": "string", "title": "Description", "description": "Описание задачи"},
                    "responsible_id": {"type": "integer", "title": "Responsible ID", "description": "ID ответственного пользователя"},
                    "deadline": {"type": "string", "title": "Deadline", "description": "Срок выполнения (ISO-8601)"},
                    "priority": {"type": ["integer", "string"], "title": "Priority", "description": "Приоритет задачи"},
                    # Allow custom UF_* fields and other optional properties
                },
                "patternProperties": {
                    "^UF_": {"type": ["string", "number", "array", "object"], "title": "Custom Field", "description": "UF_* custom fields"}
                },
                "additionalProperties": True
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
        """Create a task in Bitrix24.

        Supports webhook_url or domain+access_token credentials.
        """
        # Resolve credentials: follow existing integrations pattern (provider 'other' with api_key fallback)
        strategy = self.metadata.credentials_strategy or "oauth"
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy=strategy)
        if not creds:
            creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")

        if not creds:
            await logger.error("Bitrix24 credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "Bitrix24 credentials not found"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            payload = creds if isinstance(creds, dict) else {}

        webhook = payload.get("webhook_url") or payload.get("webhook")
        domain = payload.get("domain") or payload.get("base_url") or payload.get("url")
        token = payload.get("access_token") or payload.get("token") or payload.get("accessToken")

        # Validate and build fields
        title = config.get("title") or config.get("TITLE")
        if not title:
            await logger.error("title is required")
            return {"response": {"ok": False, "error_code": 400, "description": "title is required"}}

        # Build Bitrix fields (tasks API expects 'fields' object)
        fields: Dict[str, Any] = {}
        fields["TITLE"] = title

        description = config.get("description") or config.get("DESCRIPTION")
        if description is not None:
            fields["DESCRIPTION"] = description

        responsible = config.get("responsible_id") or config.get("RESPONSIBLE_ID")
        if responsible is not None:
            try:
                fields["RESPONSIBLE_ID"] = int(responsible)
            except Exception:
                fields["RESPONSIBLE_ID"] = responsible

        deadline = config.get("deadline") or config.get("DEADLINE")
        if deadline is not None:
            fields["DEADLINE"] = deadline

        priority = config.get("priority") or config.get("PRIORITY")
        if priority is not None:
            fields["PRIORITY"] = priority

        # Merge other top-level keys (UF_* and arbitrary extra fields)
        for k, v in config.items():
            if k in ("title", "TITLE", "description", "DESCRIPTION", "responsible_id", "RESPONSIBLE_ID", "deadline", "DEADLINE", "priority", "PRIORITY"):
                continue
            if isinstance(k, str) and (k.startswith("UF_") or k.isupper()):
                # allow passing additional uppercase Bitrix fields or UF_* custom fields
                fields[k if k.isupper() else k.upper()] = v

        request_data = {"fields": fields}

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

        # Call Bitrix
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Try webhook first
                if webhook:
                    try:
                        url = webhook.rstrip("/") + "/tasks.task.add"
                        resp = await client.post(url, json=request_data)
                        handled = await _handle_response(resp)
                        if handled.get("ok"):
                            return {"response": {"ok": True, "result": handled.get("result")}}
                        else:
                            return {"response": {"ok": False, "error_code": 400, "description": handled.get("error")}}
                    except Exception as e:
                        await logger.error(f"Bitrix24 webhook request failed: {e}")

                # Then try domain + token
                if domain and token:
                    try:
                        base = domain.rstrip("/")
                        if not base.startswith("http"):
                            base = "https://" + base

                        url = f"{base}/rest/tasks.task.add.json"
                        params = {"auth": token}
                        resp = await client.post(url, params=params, json=request_data)
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
