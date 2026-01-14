"""Альтернативная интеграция: возвращает побочные эффекты, показания и краткую информацию.

Эту версию сделано в другом стиле — и конфиг, и структура ответа отличаются
от оригинала: отсутствует параметр `limit` в схеме, вместо него есть `detail`.
"""
from typing import Dict, Any, List
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.registry import registry


class PharmSideEffectsIntegration(BaseIntegration):
    """Интеграция, возвращающая краткие/расширенные сведения о препарате.

    Ожидает в конфиге поле `substance` (строка). Параметр `detail` может быть
    `brief` или `full`. По умолчанию `brief`.
    """

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="medicine_side_effects",
            version="2.0.0",
            name="Medicine: Side Effects & Info",
            description="Побочные эффекты, показания и краткая информация по активному веществу",
            category="medicine",
            icon_s3_key="icons/integrations/medicine_alt.svg",
            color="#336699",
            config_schema={
                "type": "object",
                "required": ["substance"],
                "properties": {
                    "substance": {"type": "string", "title": "Активное вещество (например: ibuprofen)"},
                    "detail": {"type": "string", "title": "Уровень детализации", "enum": ["brief", "full"], "default": "brief"}
                }
            },
            credentials_provider="openfda",
            credentials_strategy="api_key",
        )

    async def execute(self, config: Dict[str, Any], credentials_resolver, bot_id, logger) -> Dict[str, Any]:
        substance = (config or {}).get("substance")
        detail = (config or {}).get("detail", "brief")

        if not substance:
            await logger.warning("substance is required in config")
            return {"response": {"ok": False, "error_code": 400, "description": "substance is required"}}

        # Получаем ключ если есть — интеграция дружелюбно продолжает работу без ключа
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="openfda", strategy="api_key")
        api_key = creds.get("payload", {}).get("api_key") if creds else None

        # Для brief ограничиваемся 1 результатом, для full — до 5
        limit = 5 if detail == "full" else 1

        url = "https://api.fda.gov/drug/label.json"
        params = {
            "search": f'openfda.generic_name:"{substance}"',
            "limit": limit,
        }
        if api_key:
            params["api_key"] = api_key

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=15.0)

            if resp.status_code != 200:
                # Возвращаем текст ошибки от API
                return {"response": {"ok": False, "error_code": resp.status_code, "description": resp.text}}

            payload = resp.json()
            entries: List[Dict[str, Any]] = payload.get("results", [])

            if not entries:
                return {"response": {"ok": False, "description": "Ничего не найдено по заданному веществу"}}

            def first_snip(src, default="Нет данных", size=400):
                if not src:
                    return default
                if isinstance(src, list):
                    text = src[0]
                else:
                    text = str(src)
                return text.strip()[:size]

            results: List[Dict[str, Any]] = []
            for entry in entries:
                of = entry.get("openfda", {})
                generic = (of.get("generic_name") or [None])[0] if of else None
                brands = of.get("brand_name") if of else None

                item = {
                    "generic_name": generic or substance,
                    "brand_names": brands or [],
                    "manufacturer": (of.get("manufacturer_name") or [None])[0] if of else None,
                    "indications_snippet": first_snip(entry.get("indications_and_usage")),
                    "adverse_reactions_snippet": first_snip(entry.get("adverse_reactions")),
                    "warnings_snippet": first_snip(entry.get("warnings")),
                }

                if detail == "full":
                    # Добавляем дополнительные поля в режим full
                    item.update({
                        "dosage": first_snip(entry.get("dosage_and_administration"), size=1200),
                        "full_adverse_reactions": entry.get("adverse_reactions", []),
                        "full_indications": entry.get("indications_and_usage", []),
                    })

                results.append(item)

            # Формируем итоговую структуру — отличается от оригинальной версии
            final = {
                "query": substance,
                "detail": detail,
                "found": len(results),
                "entries": results,
            }

            return {"response": {"ok": True, "result": final}}

        except Exception as exc:  # pragma: no cover - безопасность логов
            try:
                await logger.error(f"PharmSideEffectsIntegration error: {exc}")
            except Exception:
                pass
            return {"response": {"ok": False, "error_code": 500, "description": str(exc)}}


# Регистрируем интеграцию при импорте модуля
try:
    registry.register(PharmSideEffectsIntegration())
except Exception:
    # Регистрировать не удалось — пропускаем, т.к. импорт может выполняться в тестах
    pass
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
            color="#2980b9",  # Синий цвет (отличается от зеленого/оранжевого)
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
            # Можно использовать без ключа, но стратегия прописана для совместимости
            credentials_provider="openfda",
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
        
        # Получаем ключ (если есть), но работаем и без него
        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="openfda", strategy="api_key")
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

# Если используется автоматический импорт через pkgutil, 
# эта строка всё равно нужна для явной регистрации при загрузке модуля
# Регистрация интеграции выполняется в файле пакета `app.integrations.medicine.__init__`