"""Пакет интеграций для работы с фармацевтическими данными."""
# Ничего сложного: при импорте подпакета все модули внутри зарегистрируют свои интеграции
from .get_drug_info import *  # noqa: F401, F403
"""
Medicine integrations package.
Автоматическая регистрация всех модулей в этой директории.
"""



from .get_drug_info import MedicineGetDrugInfoIntegration
from app.integrations.registry import registry

# Явная регистрация интеграций в пакете (как в других интеграциях)
try:
    registry.register(MedicineGetDrugInfoIntegration())
except Exception as e:
    print(f"Failed to register medicine integration: {e}")

__all__ = ["MedicineGetDrugInfoIntegration"]
"""Пакет интеграций для работы с фармацевтическими данными."""
# При импорте подпакета все модули внутри зарегистрируют свои интеграции
from .get_drug_info import *  # noqa: F401, F403
