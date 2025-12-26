"""Google Maps интеграции."""
from .get_elevation import GoogleMapsGetElevationIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GoogleMapsGetElevationIntegration())


