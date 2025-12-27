<<<<<<< HEAD
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
=======
"""
Пакет интеграций для работы с OpenWeatherMap API.
"""
from .get_daily_forecast import OpenweathermapGetDailyForecastIntegration

__all__ = [
    'OpenweathermapGetDailyForecastIntegration',
>>>>>>> integration/owm_get_daily_forecast
]