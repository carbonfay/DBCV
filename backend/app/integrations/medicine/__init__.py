from app.integrations.registry import registry

from .get_icd10_clinicaltables import MedicineGetICD10Integration

# Register only the ClinicalTables ICD10 integration in this branch
registry.register(MedicineGetICD10Integration())
