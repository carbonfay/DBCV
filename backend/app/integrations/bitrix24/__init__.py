"""Bitrix24 интеграции: импорт и регистрация всех реализаций."""
from .get_activity import Bitrix24GetActivityIntegration

from app.integrations.registry import registry


# Автоматическая регистрация интеграций при импорте пакета
registry.register(Bitrix24GetActivityIntegration())
