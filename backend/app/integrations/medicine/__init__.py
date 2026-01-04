from app.integrations.registry import registry

from .get_symptoms_infermedica import MedicineGetSymptomsIntegration

# Register only the Infermedica symptoms integration in this branch
registry.register(MedicineGetSymptomsIntegration())
