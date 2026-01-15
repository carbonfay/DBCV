import httpx
from typing import Dict, Any
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.registry import registry

class MedicineDrugClassificationIntegration(BaseIntegration):
    """
    Интеграция с RxNav для классификации медикаментов по системе RxNorm.
    """
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_drug_class",
            version="1.0.5",
            name="Medicine: Поиск лекарств",
            description="Определение кодов RXCUI и фармакологических групп",
            category="medicine",
            icon_s3_key="icons/integrations/medicine_rx.svg",
            color="#27ae60",
            config_schema={
                "type": "object",
                "required": ["drug_name"],
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "title": "Название препарата (English)"
                    }
                }
            },
            credentials_provider="",
            credentials_strategy="none",
            library_name=None,
            examples=[]
        )

    async def execute(self, config, credentials_resolver, bot_id, logger) -> Dict[str, Any]:
        search_term = config.get("drug_name")
        
        # Шаг 1: Поиск ID препарата (RXCUI)
        search_url = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
        
        async with httpx.AsyncClient() as session:
            try:
                # Запрашиваем идентификатор
                r = await session.get(search_url, params={"name": search_term}, timeout=12.0)
                if r.status_code != 200:
                    return {"response": {"ok": False, "description": "Ошибка связи с медицинским реестром"}}
                
                res_data = r.json()
                ids = res_data.get("idGroup", {}).get("rxnormId", [])
                
                if not ids:
                    return {"response": {"ok": False, "description": "Препарат не найден в базе RxNorm"}}
                
                target_id = ids[0]
                
                # Шаг 2: Поиск классов по ID
                class_url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json"
                class_r = await session.get(class_url, params={"rxcui": target_id}, timeout=10.0)
                
                categories = "Классификация не найдена"
                if class_r.status_code == 200:
                    c_data = class_r.json()
                    concepts = c_data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", [])
                    if concepts:
                        # Собираем уникальные названия классов
                        unique_classes = {c.get("rxclassMinConceptItem", {}).get("className") for c in concepts}
                        categories = ", ".join(list(unique_classes)[:3])

                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "Drug": search_term.title(),
                            "RXCUI": target_id,
                            "Classes": categories
                        }
                    }
                }

            except Exception as e:
                logger.error(f"RxNav Integration error: {e}")
                return {"response": {"ok": False, "description": "Внутренняя ошибка при обработке данных"}}

# Автоматическая регистрация
try:
    registry.register(MedicineDrugClassificationIntegration())
except Exception:
    pass