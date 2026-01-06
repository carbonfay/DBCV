"""Внутренние интеграции DBCV системы."""
from .get_subscribers import GetSubscribersIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GetSubscribersIntegration())

__all__ = ["GetSubscribersIntegration"]

