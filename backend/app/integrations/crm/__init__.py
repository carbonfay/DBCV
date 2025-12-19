"""CRM интеграции."""
from .create_contact import HubSpotCreateContactIntegration
from .get_contact import HubSpotGetContactIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(HubSpotCreateContactIntegration())
registry.register(HubSpotGetContactIntegration())
