from app.integrations.registry import registry

from .get_doctor_info_npi_registry import MedicineGetDoctorInfoIntegration

# Register only the NPI Registry doctor info integration in this branch
registry.register(MedicineGetDoctorInfoIntegration())
