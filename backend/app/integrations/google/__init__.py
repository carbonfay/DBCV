"""Google Maps integrations."""
from .maps_geocode import GoogleMapsGeocodeIntegration
from app.integrations.registry import registry


registry.register(GoogleMapsGeocodeIntegration())
