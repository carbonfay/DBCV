"""AmoCRM Get Status integration using httpx for direct API calls."""
from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class AmoCrmGetStatusIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_get_status",
            version="1.0.0",
            name="AmoCRM Get Status",
            description="Get statuses for a pipeline in AmoCRM",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#ff6c00",
            config_schema={
                "type": "object",
                            "required": ["subdomain", "pipeline_id"],
                            "properties": {
                                "subdomain": {"type": "string", "title": "Subdomain"},
                                "pipeline_id": {"type": "number", "title": "Pipeline ID"},
                                "entity_type": {"type": "string", "title": "Entity Type", "enum": ["leads", "contacts", "customers"], "default": "leads"}
                            }
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name=None,
            examples=[
                {"title": "Get pipeline statuses", "config": {"subdomain": "mycompany", "pipeline_id": 123}}
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        # Resolve credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="amocrm",
            strategy="oauth"
        )

        if not creds:
            await logger.error("AmoCRM credentials not found")
            return {"response": {"ok": False, "error_code": 401, "description": "AmoCRM credentials not found"}}

        payload = creds.get("payload", {}) or creds

        subdomain = config.get("subdomain") or payload.get("base_domain")
        if subdomain and subdomain.endswith(".amocrm.ru"):
            base_domain = subdomain
        elif subdomain:
            base_domain = f"{subdomain}.amocrm.ru"
        else:
            await logger.error("subdomain is required in config or credentials payload")
            return {"response": {"ok": False, "error_code": 400, "description": "subdomain is required"}}

        pipeline_id = config.get("pipeline_id")
        entity_type = config.get("entity_type") or "leads"
        if not pipeline_id:
            await logger.error("pipeline_id is required in config")
            return {"response": {"ok": False, "error_code": 400, "description": "pipeline_id is required"}}

        access_token = payload.get("access_token")
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        refresh_token = payload.get("refresh_token")
        redirect_uri = payload.get("redirect_uri")

        # Try refresh if needed
        if not access_token and refresh_token and client_id and client_secret:
            try:
                token_url = f"https://{base_domain}/oauth2/access_token"
                token_payload = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }
                if redirect_uri:
                    token_payload["redirect_uri"] = redirect_uri

                async with httpx.AsyncClient(timeout=20) as client:
                    r = await client.post(token_url, json=token_payload)
                    r.raise_for_status()
                    j = r.json()
                access_token = j.get("access_token")
            except httpx.HTTPError as e:
                await logger.error(f"Failed to refresh AmoCRM token: {e}")
                return {"response": {"ok": False, "error_code": 401, "description": f"token refresh failed: {str(e)}"}}

        if not access_token:
            await logger.error("access_token not found in credentials and could not be refreshed")
            return {"response": {"ok": False, "error_code": 401, "description": "access_token not found"}}

        try:
            # Use the verified endpoint with entity_type: /api/v4/{entity_type}/pipelines/{id}?with=statuses
            url = f"https://{base_domain}/api/v4/{entity_type}/pipelines/{pipeline_id}?with=statuses"
            headers = {"Authorization": f"Bearer {access_token}"}
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
                j = r.json()

            return {"response": {"ok": True, "result": j}}
        except httpx.HTTPStatusError as e:
            await logger.error(f"AmoCRM API error: {e}")
            code = e.response.status_code if e.response is not None else 500
            return {"response": {"ok": False, "error_code": code, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error when getting statuses: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
