"""OpenWeatherMap интеграции."""
from .get_forecast import OpenweathermapGetForecastIntegration
from .get_daily_forecast import OpenweathermapGetDailyForecastIntegration
from .get_air_pollution import OpenweathermapGetAirPollutionIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(OpenweathermapGetForecastIntegration())
registry.register(OpenweathermapGetDailyForecastIntegration())
registry.register(OpenweathermapGetAirPollutionIntegration())
