from app.integrations.registry import registry

from .get_articles_pubmed import MedicineGetArticlesIntegration

# Register only the PubMed articles integration in this branch
registry.register(MedicineGetArticlesIntegration())

