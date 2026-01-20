"""CMS Provider-Data integration for pharmacy info by NPI."""
from typing import Dict, Any
from uuid import UUID
import logging
import os

# Опциональный импорт httpx — если отсутствует, выполнение вернёт понятную ошибку
try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    httpx = None
    HTTPX_AVAILABLE = False

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.registry import registry
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

logger = logging.getLogger(__name__)


class MedicineGetPharmacyInfoCMSIntegration(BaseIntegration):
    """Получение информации об аптеке по NPI через CMS provider-data (datastore POS)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_pharmacy_info_cms",
            version="1.0.0",
            name="Medicine: Get Pharmacy Info (CMS provider-data)",
            description="Информация об аптеке по NPI через CMS provider-data (Provider of Services)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#2E8B57",
            config_schema={
                "type": "object",
                "required": ["npi"],
                "properties": {
                    "npi": {"type": "string", "title": "Pharmacy NPI", "description": "10-digit NPI"},
                    "state": {"type": "string", "title": "State (optional)", "minLength": 2, "maxLength": 2}
                }
            },
            credentials_provider="medicine",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not HTTPX_AVAILABLE:
            return {"response": {"ok": False, "description": "httpx library is not installed"}}

        # Попытка получить credentials; если их нет — допускаем анонимный запрос
        app_token = None
        try:
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id, provider="medicine", strategy="api_key"
            )
        except Exception:
            creds = None

        if creds:
            payload = creds.get("payload", creds)
            app_token = payload.get("app_token") or payload.get("X-App-Token")

        # Если креды не найдены у резолвера — читать токен из переменной окружения
        if not app_token:
            app_token = os.getenv("MEDICINE_APP_TOKEN")


        npi = config.get("npi") or config.get("provider_id")
        if not npi:
            await logger.error("npi is required in config")
            return {"response": {"ok": False, "error_code": 400, "description": "npi is required"}}

        state = config.get("state")

        # Debug logging: record received config and npi
        try:
            await logger.info(f"MedicineGetPharmacyInfoCMSIntegration: received config={config}")
        except Exception:
            # In case BotLogger isn't available synchronously, also log to standard logging
            logging.getLogger(__name__).info(f"MedicineGetPharmacyInfoCMSIntegration: received config={config}")

        # CMS provider-data POS datastore (dataset id used here corresponds to POS)
        url = "https://data.cms.gov/provider-data/api/1/datastore/query/ynj2-r877/0"
        headers = {"Accept": "application/json"}
        if app_token:
            headers["X-App-Token"] = app_token
        filters = [{"column": "npi", "operator": "eq", "value": str(npi)}]
        if state:
            filters.append({"column": "state", "operator": "eq", "value": state.upper()})

        # allow overriding limit via config; default to 2 to return a couple of related records
        try:
            limit_val = int(config.get("limit", 2))
        except Exception:
            limit_val = 2
        payload_query = {"filter": filters, "includeTotal": True, "limit": limit_val}
        # Log the payload_query for debugging
        try:
            await logger.info(f"MedicineGetPharmacyInfoCMSIntegration: payload_query={payload_query}")
        except Exception:
            logging.getLogger(__name__).info(f"MedicineGetPharmacyInfoCMSIntegration: payload_query={payload_query}")

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # Если есть app_token — используем CMS provider-data POST
                if app_token:
                    resp = await client.post(url, headers=headers, json=payload_query)
                    # Debug response
                    try:
                        await logger.info(f"CMS POST status={resp.status_code}")
                    except Exception:
                        logging.getLogger(__name__).info(f"CMS POST status={resp.status_code}")
                    try:
                        logging.getLogger(__name__).debug(f"CMS POST response text: {resp.text}")
                    except Exception:
                        pass

                    if resp.status_code == 200:
                        data = resp.json()
                        results = data.get("results", [])
                        if not results:
                            return {"response": {"ok": False, "error_code": 404, "description": "Pharmacy not found"}}
                        # build aggregated facilities grouped by facility_id
                        facilities_map = {}
                        for r in results:
                            fid = r.get("facility_id") or r.get("npi") or "unknown"
                            if fid not in facilities_map:
                                facilities_map[fid] = {
                                    "facility_id": fid,
                                    "facility_name": r.get("facility_name"),
                                    "address": r.get("address"),
                                    "citytown": r.get("citytown"),
                                    "state": r.get("state"),
                                    "zip_code": r.get("zip_code"),
                                    "countyparish": r.get("countyparish"),
                                    "telephone_number": r.get("telephone_number"),
                                    "measures": []
                                }
                            # aggregate measure-level fields
                            measure = {
                                "measure_id": r.get("measure_id"),
                                "measure_name": r.get("measure_name"),
                                "compared_to_national": r.get("compared_to_national"),
                                "denominator": r.get("denominator"),
                                "score": r.get("score"),
                                "lower_estimate": r.get("lower_estimate"),
                                "higher_estimate": r.get("higher_estimate"),
                                "footnote": r.get("footnote"),
                                "start_date": r.get("start_date"),
                                "end_date": r.get("end_date")
                            }
                            facilities_map[fid]["measures"].append(measure)

                        facilities = list(facilities_map.values())
                        # by default return single aggregated facility; use config['all']=True to return full list
                        if config.get("all"):
                            info = {"results": results, "facilities": facilities, "used_app_token": True}
                        else:
                            # If a state filter was provided in config, prefer facility with matching state
                            chosen = None
                            cfg_state = state
                            if cfg_state and facilities:
                                cfg_state_up = cfg_state.upper()
                                for f in facilities:
                                    f_state = f.get("state")
                                    if f_state and f_state.upper() == cfg_state_up:
                                        chosen = f
                                        break
                            if not chosen:
                                chosen = facilities[0] if facilities else None
                            info = {"facility": chosen, "used_app_token": True}
                        return {"response": {"ok": True, "result": info}}
                    return {"response": {"ok": False, "error_code": resp.status_code, "description": resp.text}}

                # Без токена — fallback на публичный NPPES (npiregistry) API
                npp_url = "https://npiregistry.cms.hhs.gov/api/"
                npp_params = {"number": str(npi), "version": "2.1"}
                resp = await client.get(npp_url, params=npp_params, timeout=20.0)
                # Debug response
                try:
                    await logger.info(f"NPPES GET status={resp.status_code} params={npp_params}")
                except Exception:
                    logging.getLogger(__name__).info(f"NPPES GET status={resp.status_code} params={npp_params}")
                try:
                    logging.getLogger(__name__).debug(f"NPPES GET response text: {resp.text}")
                except Exception:
                    pass

                if resp.status_code != 200:
                    return {"response": {"ok": False, "description": f"NPPES API Error: {resp.status_code}"}}
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    return {"response": {"ok": False, "error_code": 404, "description": "Pharmacy not found (NPPES)"}}
                item = results[0]
                basic = item.get("basic", {})
                addr_list = item.get("addresses", [])
                addr_obj = next((a for a in addr_list if a.get("address_purpose") == "LOCATION"), addr_list[0] if addr_list else {})
                full_address = f"{addr_obj.get('address_1','')}, {addr_obj.get('city','')}, {addr_obj.get('state','')} {addr_obj.get('postal_code','')}".strip(', ')
                rec = {
                    "npi": item.get("npi"),
                    "facility_name": basic.get("organization_name") or f"{basic.get('first_name','')} {basic.get('last_name','')}".strip(),
                    "address": full_address,
                    "state": addr_obj.get('state') or None,
                    "type": "Organization" if item.get('enumeration_type') == 'NPI-2' else 'Individual',
                    "status": "Active" if basic.get('status') == 'A' else 'Inactive'
                }
                # return as a list and aggregate for consistency with CMS path
                facilities_map = {}
                fid = rec.get("npi") or rec.get("npi") or "unknown"
                facilities_map[fid] = {
                    "facility_id": fid,
                    "facility_name": rec.get("facility_name"),
                    "address": rec.get("address"),
                    "state": rec.get("state"),
                    "zip_code": rec.get("zip_code"),
                    "measures": []
                }
                facilities = list(facilities_map.values())
                if config.get("all"):
                    info = {"results": [rec], "facilities": facilities, "used_app_token": False}
                else:
                    # prefer facility matching config state when available
                    chosen = None
                    cfg_state = state
                    if cfg_state and facilities:
                        cfg_state_up = cfg_state.upper()
                        for f in facilities:
                            f_state = f.get("state")
                            if f_state and f_state.upper() == cfg_state_up:
                                chosen = f
                                break
                    if not chosen:
                        chosen = facilities[0] if facilities else None
                    info = {"facility": chosen, "used_app_token": False}
                return {"response": {"ok": True, "result": info}}
            except httpx.RequestError as e:
                await logger.error(f"Request error: {e}")
                return {"response": {"ok": False, "error_code": 500, "description": str(e)}}


# Регистрируем интеграцию
registry.register(MedicineGetPharmacyInfoCMSIntegration())
