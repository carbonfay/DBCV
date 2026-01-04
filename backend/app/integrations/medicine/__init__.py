from app.integrations.registry import registry

from .get_disease_info_who_icd import MedicineGetDiseaseInfoIntegration

# Register only the WHO ICD disease info integration in this branch
registry.register(MedicineGetDiseaseInfoIntegration())
