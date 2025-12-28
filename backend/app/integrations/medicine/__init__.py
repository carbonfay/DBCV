from app.integrations.registry import registry

from .get_articles import MedicineGetArticlesIntegration
from .get_trials import MedicineGetTrialsIntegration

registry.register(MedicineGetArticlesIntegration())
registry.register(MedicineGetTrialsIntegration())
