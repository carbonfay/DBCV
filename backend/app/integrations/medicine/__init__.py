from app.integrations.registry import registry

from .get_pharmacy_info_cms_provider_data import MedicineGetPharmacyInfoIntegration

# Register only the CMS provider-data pharmacy info integration in this branch
registry.register(MedicineGetPharmacyInfoIntegration())
