import httpx
from typing import Dict, Any
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.registry import registry

class MedicineGetDrugInfoIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_drug_info",
            version="1.0.0",
            name="Medicine: Get Drug Info",
            description="Детальная информация о препарате по активному веществу",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#27ae60",
            config_schema={
                "type": "object",
                "required": ["generic_name"],
                "properties": {
                    "generic_name": {"type": "string", "title": "Активное вещество (например: Ibuprofen)"},
                    "limit": {"type": "integer", "default": 1, "title": "Лимит результатов"}
                }
            },
            credentials_provider="openfda",
            credentials_strategy="api_key"
        )

    async def execute(self, config, credentials_resolver, bot_id, logger) -> Dict[str, Any]:
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="openfda", strategy="api_key")
        api_key = creds.get("payload", {}).get("api_key") if creds else ""

        url = "https://api.fda.gov/drug/label.json"
        params = {
            "api_key": api_key,
            "search": f"openfda.generic_name:\"{config.get('generic_name')}\"",
            "limit": config.get("limit", 1)
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=15.0)

        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                drug = results[0]
                info = {
                    "Generic Name": drug.get("openfda", {}).get("generic_name", ["Unknown"])[0],
                    "Manufacturer": drug.get("openfda", {}).get("manufacturer_name", ["Unknown"])[0],
                    "Warnings": (drug.get("warnings", ["No warnings"])[0])[:500]
                }
                return {"response": {"ok": True, "result": info}}
            return {"response": {"ok": False, "description": "Ничего не найдено"}}
        return {"response": {"ok": False, "error_code": resp.status_code, "description": resp.text}}

# Саморегистрация — именно её "дёргает" importlib.import_module
try:
    registry.register(MedicineGetDrugInfoIntegration())
except Exception:
    pass
