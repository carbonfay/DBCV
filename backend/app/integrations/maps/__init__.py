"""Maps интеграции."""
from .geocoding import GoogleMapsGeocodingIntegration
from .route import GoogleMapsRouteIntegration
from .geocode import GoogleMapsGeocodeIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GoogleMapsGeocodingIntegration())
registry.register(GoogleMapsRouteIntegration())
registry.register(GoogleMapsGeocodeIntegration())
