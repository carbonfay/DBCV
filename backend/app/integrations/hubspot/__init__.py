"""HubSpot интеграции."""
from .create_deal import HubSpotCreateDealIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(HubSpotCreateDealIntegration())

