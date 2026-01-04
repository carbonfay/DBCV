from app.integrations.registry import registry

from .search_drugs_rxnav import MedicineSearchDrugsIntegration

# Register only the RxNav drugs search integration in this branch
registry.register(MedicineSearchDrugsIntegration())
