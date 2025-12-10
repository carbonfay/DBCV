"""Яндекс.Погода интеграции."""
from .get_forecast import YandexWeatherGetForecastIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YandexWeatherGetForecastIntegration())
