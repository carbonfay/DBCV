"""Medicine интеграции."""
from .get_icd10 import MedicineGetIcd10Integration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(MedicineGetIcd10Integration())

