"""ICD-10 lookup integration using `httpx`.

Возвращает объединённую информацию по коду ICD-10 из двух источников:
- NLM ClinicalTables (https://clinicaltables.nlm.nih.gov)
- icd10api.com (https://icd10api.com)

Интеграция всегда вызывает `credentials_resolver.get_default_for()` (provider: "medicine").
Если в credentials есть `api_key`, он будет передан как Bearer для сервисов.
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
    """Интеграция для поиска расширённой информации по ICD-10 коду."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_icd10",
            version="1.0.0",
            name="Medicine Get ICD10",
            description="Поиск расширённой информации по коду ICD-10 (несколько источников)",
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
                        "description": "Код ICD-10, например 'J45' или 'A00'"
                    },
                    "clinicaltables_url": {
                        "type": "string",
                        "title": "ClinicalTables URL",
                        "default": "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search",
                        "description": "NLM ClinicalTables API base URL"
                    },
                    "icd10api_url": {
                        "type": "string",
                        "title": "ICD10API URL",
                        "default": "https://icd10api.com/?s={code}",
                        "description": "Внешний сервис icd10api.com (в виде шаблона с {code})"
                    },
                    "max_list": {
                        "type": "integer",
                        "title": "Max results",
                        "default": 3
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {"title": "ICD-10 info (J45)", "config": {"code": "J45"}}
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Выполняет поиск ICD-10 кода в нескольких источниках и объединяет данные."""
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available for medicine_get_icd10 integration")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        # Получаем credentials (обязательно вызывать)
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="medicine",
            strategy="api_key",
        )

        api_key = None
        if creds:
            payload = creds.get("payload", {}) or creds
            api_key = payload.get("api_key") or payload.get("key")

        code = str(config.get("code", "")).strip()
        if not code:
            await logger.error("ICD-10 code (config['code']) is required")
            return {
                "response": {"ok": False, "error_code": 400, "description": "ICD-10 code (config['code']) is required"}
            }

        clinical_url = config.get("clinicaltables_url", "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search")
        icd10api_template = config.get("icd10api_url", "https://icd10api.com/?s={code}")
        max_list = int(config.get("max_list", 3))

        sources = []
        combined: Dict[str, Any] = {"query_code": code, "found": False, "sources": {}}

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1) NLM ClinicalTables
                params = {"sf": "code", "terms": code, "maxList": max_list}
                try:
                    ct_resp = await client.get(clinical_url, params=params, headers=headers)
                    sources.append({"name": "clinicaltables", "url": str(ct_resp.url), "status": ct_resp.status_code})
                    ct_data = None
                    if ct_resp.status_code == 200:
                        try:
                            ct_data = ct_resp.json()
                        except Exception:
                            ct_data = {"text": ct_resp.text}
                    else:
                        ct_data = {"error": f"status {ct_resp.status_code}", "text": ct_resp.text}

                except httpx.HTTPError as e:
                    await logger.error(f"ClinicalTables http error: {e}")
                    ct_data = {"error": str(e)}

                # Попытка распарсить clinicaltables
                clinical_parsed: Dict[str, Any] = {"raw": ct_data}
                try:
                    if isinstance(ct_data, list) and len(ct_data) >= 2:
                        codes = ct_data[0] or []
                        descriptions = ct_data[1] or []
                        clinical_parsed.update({
                            "codes": codes,
                            "descriptions": descriptions,
                            "primary_description": descriptions[0] if descriptions else None
                        })
                        if codes:
                            combined["found"] = True
                except Exception:
                    clinical_parsed["parse_error"] = True

                combined["sources"]["clinicaltables"] = clinical_parsed

                # 2) icd10api.com (fallback / additional details)
                try:
                    if "{code}" in icd10api_template:
                        icd10api_url = icd10api_template.format(code=code)
                    else:
                        icd10api_url = icd10api_template.rstrip("/")
                        if "?" in icd10api_url:
                            icd10api_url = f"{icd10api_url}&s={code}"
                        else:
                            icd10api_url = f"{icd10api_url}/?s={code}"

                    icd_resp = await client.get(icd10api_url, headers=headers)
                    sources.append({"name": "icd10api", "url": str(icd_resp.url), "status": icd_resp.status_code})
                    try:
                        icd_data = icd_resp.json()
                    except Exception:
                        icd_data = {"text": icd_resp.text}

                except httpx.HTTPError as e:
                    await logger.error(f"icd10api http error: {e}")
                    icd_data = {"error": str(e)}

                combined["sources"]["icd10api"] = icd_data

                # Попробуем извлечь полезные поля из icd10api (если есть)
                try:
                    if isinstance(icd_data, dict):
                        # Пример полей: {'Code': 'A00', 'Desc': 'Cholera', ...}
                        primary_desc = icd_data.get("Desc") or icd_data.get("Description")
                        combined.update({
                            "primary_description": combined.get("primary_description") or primary_desc,
                            "icd10_details": icd_data,
                        })
                        if icd_data.get("Code"):
                            combined["found"] = True
                except Exception:
                    combined.setdefault("notes", []).append("failed_to_extract_icd10api_fields")

        except Exception as e:
            await logger.error(f"Unexpected error while fetching ICD-10 data: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}

        # Формируем итог
        result = {
            "query": code,
            "found": combined.get("found", False),
            "primary_description": combined.get("primary_description"),
            "sources": combined.get("sources", {}),
            "merged": combined,
        }

        return {"response": {"ok": True, "result": result}}
"""Integration: Получение информации по коду ICD-10 (ICD10).

Использует публичный NLM ClinicalTables API для поиска описания кода ICD-10.
Если доступна библиотека `httpx`, используется она (async). В противном случае
возвращается ошибка с указанием, что библиотека не установлена.

API запрос: GET https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?sf=code&terms={code}&maxList=1
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx напрямую
try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    httpx = None
    HTTPX_AVAILABLE = False


class MedicineGetIcd10Integration(BaseIntegration):
    """Интеграция для поиска описания ICD-10 кода."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_icd10",
            version="1.0.0",
            name="Medicine Get ICD10",
            description="Поиск описания по коду ICD-10 (использует NLM ClinicalTables public API)",
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
                        "description": "Код ICD-10, например 'J45' или 'A00'"
                    },
                    "api_base_url": {
                        "type": "string",
                        "title": "API Base URL",
                        "description": "URL API для поиска (по умолчанию NLM ClinicalTables)",
                        "default": "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
                    },
                    "max_list": {
                        "type": "integer",
                        "title": "Max results",
                        "description": "Максимальное количество возвращаемых записей",
                        "default": 1
                    }
                }
            },
            credentials_provider="medicine",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить описание кода",
                    "config": {"code": "J45"}
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Выполняет поиск ICD-10 кода через NLM ClinicalTables API.

        Args:
            config: Параметры интеграции (см. config_schema)
            credentials_resolver: резолвер credentials (требование платформы — всегда вызывать)
            bot_id: id бота
            logger: логгер

        Returns:
            dict в формате платформы: {"response": {"ok": True/False, "result"/...}}
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available for medicine_get_icd10 integration")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        # Получаем credentials (если есть) — согласно требованию всегда вызывать резолвер
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="medicine",
            strategy="api_key",
        )

        api_key = None
        if creds:
            payload = creds.get("payload", {}) or creds
            api_key = payload.get("api_key") or payload.get("key")

        code = config.get("code")
        if not code:
            await logger.error("ICD-10 code (config['code']) is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "ICD-10 code (config['code']) is required"
                }
            }

        api_base = config.get(
            "api_base_url", "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
        )
        max_list = int(config.get("max_list", 1))

        params = {"sf": "code", "terms": str(code), "maxList": max_list}
        headers = {}
        if api_key:
            # Попробуем добавить в заголовок Bearer — для совместимости с API, требующими key
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

            # NLM ClinicalTables возвращает массивы, где:
            # data[0] - список кодов, data[1] - список описаний
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

            result = {
                "query_code": code,
                "found": bool(code_list),
                "codes": code_list,
                "description": description,
                "raw": data,
            }

            return {"response": {"ok": True, "result": result}}

        except httpx.HTTPError as e:
            await logger.error(f"HTTP error while fetching ICD10 data: {e}")
            return {"response": {"ok": False, "error_code": 502, "description": str(e)}}
        except Exception as e:
            await logger.error(f"Unexpected error in medicine_get_icd10: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
