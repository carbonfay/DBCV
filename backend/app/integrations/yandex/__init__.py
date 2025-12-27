"""Yandex integrations package."""
from .maps_search import YandexMapsSearchIntegration
from app.integrations.registry import registry

# Register the integration
registry.register(YandexMapsSearchIntegration())

__all__ = [
    'YandexMapsSearchIntegration',
]
