"""AmoCRM Get Pipeline integration using httpx for direct API calls."""
from typing import Dict, Any
from uuid import UUID

import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class AmoCrmGetPipelineIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="amocrm_get_pipeline",
            version="1.0.0",
            name="AmoCRM Get Pipeline",
            description="Get pipelines or a single pipeline from AmoCRM",
            category="crm",
            icon_s3_key="icons/integrations/amocrm.svg",
            color="#ff6c00",
            config_schema={
                "type": "object",
                    "required": ["subdomain"],
                    "properties": {
                        "subdomain": {"type": "string", "title": "Subdomain"},
                        "pipeline_id": {"type": "number", "title": "Pipeline ID"},
                        "entity_type": {"type": "string", "title": "Entity Type", "enum": ["leads", "contacts", "customers"], "default": "leads"},
                        "with_statuses": {"type": "boolean", "title": "Include statuses", "default": False}
                    }
            },
            credentials_provider="amocrm",
            credentials_strategy="oauth",
            library_name=None,
            examples=[
                {"title": "List pipelines", "config": {"subdomain": "mycompany"}},
                {"title": "Get pipeline by id", "config": {"subdomain": "mycompany", "pipeline_id": 123}}
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
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
        with_statuses = bool(config.get("with_statuses"))

        access_token = payload.get("access_token")
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        refresh_token = payload.get("refresh_token")
        redirect_uri = payload.get("redirect_uri")

        # If no access_token, try to refresh
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
            # Build URL using entity_type and optional with=statuses
            base_path = f"/api/v4/{entity_type}/pipelines"
            if pipeline_id:
                url = f"https://{base_domain}{base_path}/{pipeline_id}"
            else:
                url = f"https://{base_domain}{base_path}"
            if with_statuses:
                sep = '&' if '?' in url else '?'
                url = f"{url}{sep}with=statuses"

            headers = {"Authorization": f"Bearer {access_token}"}
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
                j = r.json()

            # Normalize response: always return a list under 'pipelines'
            pipelines = []
            if pipeline_id:
                # Single pipeline expected: API may return object or wrapped dict
                if isinstance(j, dict) and "id" in j:
                    pipelines = [j]
                else:
                    embedded = j.get("_embedded") if isinstance(j, dict) else None
                    pipelines = (embedded.get("pipelines") if embedded else None) or j.get("pipelines") if isinstance(j, dict) else []
                    if isinstance(pipelines, dict):
                        # sometimes embedded pipelines provided as dict
                        pipelines = [pipelines]
                    if not pipelines and isinstance(j, list):
                        pipelines = j
            else:
                # Listing pipelines: common AmoCRM responses use _embedded.pipelines
                if isinstance(j, dict):
                    embedded = j.get("_embedded") or {}
                    pipelines = embedded.get("pipelines") or j.get("pipelines") or []
                elif isinstance(j, list):
                    pipelines = j

            # Ensure pipelines is a list
            if pipelines is None:
                pipelines = []

            return {"response": {"ok": True, "result": {"pipelines": pipelines}}}
        except httpx.HTTPStatusError as e:
            await logger.error(f"AmoCRM API error: {e}")
            code = e.response.status_code if e.response is not None else 500
            return {"response": {"ok": False, "error_code": code, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error when getting pipelines: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
