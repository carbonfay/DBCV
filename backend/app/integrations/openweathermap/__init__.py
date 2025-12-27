"""OpenWeatherMap интеграции."""
from .get_uv_index import OpenweathermapGetUvIndexIntegration
from .get_air_pollution import OpenweathermapGetAirPollutionIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(OpenweathermapGetUvIndexIntegration())
# registry.register(OpenweathermapGetAirPollutionIntegration())  # Раскомментировать, если нужно

__all__ = [
    'OpenweathermapGetUvIndexIntegration',
    'OpenweathermapGetAirPollutionIntegration',
]