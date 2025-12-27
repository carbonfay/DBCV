"""Yandex интеграции."""
from .maps_geocode import YandexMapsGeocodeIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YandexMapsGeocodeIntegration())
