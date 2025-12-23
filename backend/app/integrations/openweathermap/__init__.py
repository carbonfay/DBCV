"""OpenWeatherMap интеграции."""
from .get_uv_index import OpenWeatherMapGetUvIndexIntegration
from app.integrations.registry import registry

# Регистрируем интеграции OpenWeatherMap
registry.register(OpenWeatherMapGetUvIndexIntegration())