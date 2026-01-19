"""Medicine ICD-10 integration using NLM ClinicalTables (httpx).

Provides `MedicineGetIcd10Integration` which queries NLM ClinicalTables
for ICD-10 code descriptions. Returns platform response format.
"""
from typing import Dict, Any, Optional
"""Medicine ICD-10 integration using NLM ClinicalTables (httpx).

Returns the external API JSON directly as the platform `response`.
If credentials with `api_key` are present, the integration will send
an `Authorization: Bearer <api_key>` header.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False


class MedicineGetIcd10Integration(BaseIntegration):
    """Lookup ICD-10 code via NLM ClinicalTables and return raw JSON."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_icd10",
            version="1.0.0",
            name="Medicine Get ICD10",
            description="Lookup ICD-10 description using NLM ClinicalTables public API",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#6f42c1",
            config_schema={
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {"type": "string", "title": "ICD-10 Code"},
                    "api_base_url": {
                        "type": "string",
                        "title": "API Base URL",
                        "default": "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search",
                    },
                    "max_list": {"type": "integer", "default": 1},
                },
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name=("httpx>=0.27.0" if HTTPX_AVAILABLE else None),
            examples=[{"title": "Lookup ICD-10", "config": {"code": "J45"}}],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available for medicine_get_icd10 integration")
            return {"response": {"ok": False, "error_code": 500, "description": "httpx not installed"}}

        # Resolve optional API key from credentials
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")
        api_key: Optional[str] = None
        if creds:
            payload = creds.get("payload", {}) or creds
            api_key = payload.get("api_key") or payload.get("key")

        code = config.get("code")
        if not code:
            await logger.error("ICD-10 code (config['code']) is required")
            return {"response": {"ok": False, "error_code": 400, "description": "ICD-10 code required"}}

        api_base = config.get("api_base_url", "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search")
        try:
            max_list = int(config.get("max_list", 1))
        except Exception:
            max_list = 1

        params = {"sf": "code", "terms": str(code), "maxList": max_list}
        headers: Dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_base, params=params, headers=headers)

            # If API returned JSON, return it directly under `response`.
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    # Not valid JSON, return raw text
                    return {"response": {"ok": False, "error_code": 502, "description": "Invalid JSON from ICD10 API", "text": resp.text}}

                return {"response": data}

            # Non-200: return structured error
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            await logger.error(f"ICD10 API returned status {resp.status_code}: {err}")
            return {"response": {"ok": False, "error_code": resp.status_code, "error": err}}

        except httpx.HTTPError as e:
            await logger.error(f"HTTP error while fetching ICD10 data: {e}")
            return {"response": {"ok": False, "error_code": 502, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error in medicine_get_icd10: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    httpx = None
    HTTPX_AVAILABLE = False


class MedicineGetIcd10Integration(BaseIntegration):
    """Integration: lookup ICD-10 code via NLM ClinicalTables."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_icd10",
            version="1.0.0",
            name="Medicine Get ICD10",
            description="Lookup ICD-10 description using NLM ClinicalTables public API",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#6f42c1",
            config_schema={
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {
                        "type": "string",
                        "title": "ICD-10 Code",
                        "description": "ICD-10 code (e.g. J45, A00)"
                    },
                    "api_base_url": {
                        "type": "string",
                        "title": "API Base URL",
                        "description": "Base URL for the ICD-10 lookup API",
                        "default": "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
                    },
                    "max_list": {
                        "type": "integer",
                        "title": "Max results",
                        "default": 1
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[{"title": "Lookup ICD-10", "config": {"code": "J45"}}],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Execute ICD-10 lookup and return platform response format."""
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available for medicine_get_icd10 integration")
            return {"response": {"ok": False, "error_code": 500, "description": "httpx library is not installed"}}

        # async resolve credentials (may be None)
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")
        api_key = None
        if creds:
            payload = creds.get("payload", {}) or creds
            api_key = payload.get("api_key") or payload.get("key")

        code = config.get("code")
        if not code:
            await logger.error("ICD-10 code (config['code']) is required")
            return {"response": {"ok": False, "error_code": 400, "description": "ICD-10 code (config['code']) is required"}}

        api_base = config.get("api_base_url", "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search")
        try:
            max_list = int(config.get("max_list", 1))
        except Exception:
            max_list = 1

        params = {"sf": "code", "terms": str(code), "maxList": max_list}
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_base, params=params, headers=headers)

            if resp.status_code != 200:
                await logger.error(f"ICD10 API returned status {resp.status_code}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": resp.status_code,
                        "description": f"ICD10 API returned status {resp.status_code}",
                        "response_text": resp.text,
                    }
                }

            data = resp.json()

            # NLM ClinicalTables returns arrays: data[0] codes, data[1] descriptions
            code_list = []
            description = None
            if isinstance(data, list) and len(data) >= 2:
                try:
                    code_list = data[0] or []
                    desc_list = data[1] or []
                    if code_list:
                        description = desc_list[0] if desc_list else None
                except Exception:
                    code_list = []

            result = {"query_code": code, "found": bool(code_list), "codes": code_list, "description": description, "raw": data}
            return {"response": {"ok": True, "result": result}}

        except httpx.HTTPError as e:
            await logger.error(f"HTTP error while fetching ICD10 data: {e}")
            return {"response": {"ok": False, "error_code": 502, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error in medicine_get_icd10: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
