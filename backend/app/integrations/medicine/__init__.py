from app.integrations.registry import registry

from .search_diseases_clinicaltables import MedicineSearchDiseasesIntegration

# Register only the ClinicalTables disease search integration in this branch
registry.register(MedicineSearchDiseasesIntegration())
