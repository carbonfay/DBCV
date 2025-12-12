"""Google Maps интеграции."""
from app.integrations.registry import registry
from .get_place_details import GoogleMapsGetPlaceDetailsIntegration

registry.register(GoogleMapsGetPlaceDetailsIntegration())

