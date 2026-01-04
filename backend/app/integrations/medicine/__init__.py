from app.integrations.registry import registry

from .search_pharmacies_cms_provider_data import MedicineSearchPharmaciesIntegration

# Register only the CMS provider-data pharmacies search integration in this branch
registry.register(MedicineSearchPharmaciesIntegration())
