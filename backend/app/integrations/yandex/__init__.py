from app.integrations.registry import registry

from .maps_route import YandexMapsRouteIntegration

registry.register(YandexMapsRouteIntegration())
