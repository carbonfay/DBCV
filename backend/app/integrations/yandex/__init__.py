"""Регистрация Yandex интеграций."""
from .weather_forecast import YandexWeatherForecastIntegration
from app.integrations.registry import registry

# Регистрируем интеграции
registry.register(YandexWeatherForecastIntegration())