from .get_deal import Bitrix24GetDealIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(Bitrix24GetDealIntegration())