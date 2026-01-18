from .create_contact import AmoCrmCreateContactIntegration
from app.integrations.registry import registry

registry.register(AmoCrmCreateContactIntegration())
