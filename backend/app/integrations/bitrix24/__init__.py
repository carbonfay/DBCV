"""Bitrix24 интеграции."""
from .update_contact import Bitrix24UpdateContactIntegration
from app.integrations.registry import registry

# Регистрация интеграций
registry.register(Bitrix24UpdateContactIntegration())

