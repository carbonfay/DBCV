"""NewsAPI интеграции."""

from app.integrations.registry import registry
from .get_everything import NewsApiGetEverythingIntegration

registry.register(NewsApiGetEverythingIntegration())


