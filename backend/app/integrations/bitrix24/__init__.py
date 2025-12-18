from .create_contact import Bitrix24CreateContactIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(Bitrix24CreateContactIntegration())