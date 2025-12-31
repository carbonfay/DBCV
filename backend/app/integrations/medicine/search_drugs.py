import httpx
from typing import Dict, Any
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.registry import registry

class MedicineSearchDrugsIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_search_drugs",
            version="1.0.0",
            name="Medicine: Поиск лекарства",
            description="Поиск по базе FDA (США) по названию препарата",
            category="medicine",
            icon_s3_key="icons/integrations/medicine.svg",
            color="#d35400",
            config_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "title": "Название (например: Aspirin)"},
                    "limit": {"type": "integer", "default": 1, "title": "Количество результатов"}
                }
            },
            credentials_provider="openfda",
            credentials_strategy="api_key"
        )

    async def execute(self, config, credentials_resolver, bot_id, logger) -> Dict[str, Any]:
        # 1. Получаем API ключ из настроек бота
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="openfda", strategy="api_key")
        api_key = creds.get("payload", {}).get("api_key") if creds else ""

        # 2. Формируем URL
        url = "https://api.fda.gov/drug/label.json"
        
        # 3. Параметры запроса (синтаксис OpenFDA)
        params = {
            "api_key": api_key,
            "search": f"openfda.brand_name:\"{config.get('query')}\"",
            "limit": config.get("limit", 1)
        }

        # 4. Выполняем запрос
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=15.0)
        
        # 5. Обрабатываем ответ
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            
            if results:
                drug = results[0]
                
                # Ищем описание последовательно в разных полях
                # (в FDA 'purpose' часто пуст, тогда смотрим 'indications_and_usage')
                purpose = drug.get("purpose", [])
                indications = drug.get("indications_and_usage", [])
                description_field = drug.get("description", [])

                if purpose:
                    final_desc = purpose[0]
                elif indications:
                    final_desc = indications[0]
                elif description_field:
                    final_desc = description_field[0]
                else:
                    final_desc = "Инструкция по применению доступна в базе OpenFDA."

                # Ограничиваем длину текста до 500 символов для чистоты интерфейса
                if len(final_desc) > 500:
                    final_desc = final_desc[:500] + "..."

                info = {
                    "Brand Name": drug.get("openfda", {}).get("brand_name", ["Unknown"])[0],
                    "Generic Name": drug.get("openfda", {}).get("generic_name", ["Unknown"])[0],
                    "Purpose": final_desc
                }
                return {"response": {"ok": True, "result": info}}
            
            return {"response": {"ok": False, "description": "Ничего не найдено"}}


# Регистрируем интеграцию при импорте модуля
try:
    registry.register(MedicineSearchDrugsIntegration())
except Exception:
    # Если чего-то не хватает (библиотеки) — пропускаем регистрацию
    pass