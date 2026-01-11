"""Bitrix24 интеграции."""
from .create_deal import Bitrix24CreateDealIntegration
from app.integrations.registry import registry

# Регистрация интеграций
registry.register(Bitrix24CreateDealIntegration())