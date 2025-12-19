from .get_contact import Bitrix24GetContactIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(Bitrix24GetContactIntegration())
