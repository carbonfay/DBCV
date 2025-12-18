"""OpenWeatherMap интеграции."""
from .get_uv_index import OpenweathermapGetUvIndexIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграции
registry.register(OpenweathermapGetUvIndexIntegration())
__all__ = ["OpenweathermapGetUvIndexIntegration"]
