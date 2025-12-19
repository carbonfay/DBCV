"""HubSpot интеграции."""
from .create_contact import HubSpotCreateContactIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(HubSpotCreateContactIntegration())
