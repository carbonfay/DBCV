from app.integrations.registry import registry

from .get_drug_info_rxnav import MedicineGetDrugInfoIntegration

# Register only the RxNav drug info integration in this branch
registry.register(MedicineGetDrugInfoIntegration())
