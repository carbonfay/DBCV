from app.integrations.registry import registry

from .get_trials_clinicaltrials_gov import MedicineGetTrialsIntegration

# Register only the ClinicalTrials.gov integration in this branch
registry.register(MedicineGetTrialsIntegration())
