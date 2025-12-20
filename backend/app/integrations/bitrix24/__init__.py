"""Telegram интеграции."""
from .create_company import Bitrix24CreateCompanyIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(Bitrix24CreateCompanyIntegration())
