"""OpenWeatherMap интеграции."""
from .get_uv_index import GetUVIndexIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GetUVIndexIntegration())

__all__ = ["GetUVIndexIntegration"]

