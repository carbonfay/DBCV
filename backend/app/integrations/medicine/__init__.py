"""Medicine интеграции."""
from .get_drug_info import MedicineGetDrugInfoIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграции
registry.register(MedicineGetDrugInfoIntegration())
