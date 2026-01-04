from app.integrations.registry import registry

from .get_hospital_info_cms_provider_data import MedicineGetHospitalInfoIntegration

# Register only the CMS provider-data hospital info integration in this branch
registry.register(MedicineGetHospitalInfoIntegration())
