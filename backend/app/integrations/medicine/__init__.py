from app.integrations.registry import registry

from .get_drug_interactions_openfda import MedicineGetDrugInteractionsIntegration

# Register only the OpenFDA drug interactions integration in this branch
registry.register(MedicineGetDrugInteractionsIntegration())
