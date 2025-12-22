"""NewsAPI integrations."""
from .get_top_headlines import NewsAPIGetTopHeadlines
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(NewsAPIGetTopHeadlines())
