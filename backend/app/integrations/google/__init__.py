"""Google интеграции."""
from app.integrations.registry import registry
from .get_place_details import GooglePlaceDetailsIntegration

# Регистрация интеграций
registry.register(GooglePlaceDetailsIntegration())
