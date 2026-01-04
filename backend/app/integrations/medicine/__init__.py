from app.integrations.registry import registry

from .search_doctors_npi_registry import MedicineSearchDoctorsIntegration

# Register only the NPI Registry doctors search integration in this branch
registry.register(MedicineSearchDoctorsIntegration())
