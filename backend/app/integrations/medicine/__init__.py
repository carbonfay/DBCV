from app.integrations.registry import registry

from .get_articles import MedicineGetArticlesIntegration

registry.register(MedicineGetArticlesIntegration())
