"""OpenWeatherMap интеграции."""
from .get_uv_index import OpenweathermapGetUvIndexIntegration
from .get_air_pollution import OpenweathermapGetAirPollutionIntegration
from .get_history import OpenweathermapGetWeatherHistoryIntegration
from .get_daily_forecast import OpenweathermapGetDailyForecastIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(OpenweathermapGetUvIndexIntegration())
registry.register(OpenweathermapGetAirPollutionIntegration()) 
registry.register(OpenweathermapGetWeatherHistoryIntegration()) 
registry.register(OpenweathermapGetDailyForecastIntegration()) 

__all__ = [
    'OpenweathermapGetUvIndexIntegration',
    'OpenweathermapGetAirPollutionIntegration',
    'OpenweathermapGetDailyForecastIntegration',
    'OpenweathermapGetWeatherHistoryIntegration'

]