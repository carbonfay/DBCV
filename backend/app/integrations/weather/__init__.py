"""Weather integrations package."""
from .openweathermap_daily_forecast import OpenWeatherMapDailyForecastIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(OpenWeatherMapDailyForecastIntegration())

__all__ = ["OpenWeatherMapDailyForecastIntegration"]
