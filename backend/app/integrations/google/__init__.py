from .maps_directions import GoogleMapsDirectionsIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(GoogleMapsDirectionsIntegration())
