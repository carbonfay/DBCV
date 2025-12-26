"""Google Maps интеграции."""
from .get_elevation import GoogleMapsGetElevationIntegration
from .get_place_photos import GoogleMapsGetPlacePhotosIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GoogleMapsGetElevationIntegration())
registry.register(GoogleMapsGetPlacePhotosIntegration())


