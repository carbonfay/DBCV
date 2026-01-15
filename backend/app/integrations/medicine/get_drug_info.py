import httpx
import re
from typing import Dict, Any, List
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.registry import registry

class MedicineGetDrugInfoIntegration(BaseIntegration):
    """
    Получение детальной клинической информации о препарате.
    """
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_get_drug_info",
            version="1.2.0",
            name="Medicine: Полная справка",
            description="Получение предупреждений, побочных эффектов и противопоказаний (OpenFDA)",
            category="medicine",
            icon_s3_key="icons/integrations/medicine_info.svg", # Иконка информации
            color="#2980b9",  # Синий цвет
            config_schema={
                "type": "object",
                "required": ["drug_identifier"],
                "properties": {
                    "drug_identifier": {
                        "type": "string", 
                        "title": "Название препарата (Brand Name)"
                    }
                }
            },
           
            credentials_provider="other",
            credentials_strategy="api_key"
        )

    def _clean_text(self, text_list: List[str]) -> str:
        """Вспомогательный метод для очистки медицинских текстов."""
        if not text_list:
            return "Нет данных"
        text = text_list[0]
        # Убираем лишние пробелы и переносы
        return re.sub(r'\s+', ' ', text).strip()[:500] + "..."

    async def execute(self, config, credentials_resolver, bot_id, logger) -> Dict[str, Any]:
        drug_id = config.get("drug_identifier")
        
        # Получаем ключ из провайдера 'other'
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id, 
            provider="other", 
            strategy="api_key"
        )
        api_key = creds.get("payload", {}).get("api_key") if creds else None

        url = "https://api.fda.gov/drug/label.json"
        
        # Запрос с ограничением по полям для оптимизации трафика
        params = {
            "search": f'openfda.brand_name:"{drug_id}"',
            "limit": 1
        }
        if api_key:
            params["api_key"] = api_key

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=15.0)
                
                if response.status_code == 404:
                    return {"response": {"ok": False, "description": "Инструкция для данного препарата не найдена."}}
                
                if response.status_code != 200:
                    return {"response": {"ok": False, "description": f"Ошибка сервиса FDA: {response.status_code}"}}

                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return {"response": {"ok": False, "description": "Данные отсутствуют"}}

                drug_data = results[0]

                # Извлекаем критически важные поля
                warnings = self._clean_text(drug_data.get("warnings", []))
                contraindications = self._clean_text(drug_data.get("contraindications", []))
                adverse_reactions = self._clean_text(drug_data.get("adverse_reactions", []))
                
                # Формируем итоговый объект
                result_info = {
                    "Drug": drug_data.get("openfda", {}).get("brand_name", [drug_id])[0],
                    "Warnings": warnings,
                    "Contraindications": contraindications,
                    "Side Effects": adverse_reactions
                }

                return {"response": {"ok": True, "result": result_info}}

            except Exception as e:
                logger.error(f"Drug Info Error: {e}")
                return {"response": {"ok": False, "description": "Внутренняя ошибка обработки данных"}}

# Саморегистрация — модуль регистрирует интеграцию при импорте
try:
    registry.register(MedicineGetDrugInfoIntegration())
except Exception:
    pass

