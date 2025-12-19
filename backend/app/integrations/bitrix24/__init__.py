"""Bitrix24 интеграции."""
from .create_task import Bitrix24CreateTaskIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(Bitrix24CreateTaskIntegration())
