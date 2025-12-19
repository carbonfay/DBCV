"""Bitrix24 интеграции: импорт и регистрация всех реализаций."""
from .create_task import Bitrix24CreateTaskIntegration

from app.integrations.registry import registry


registry.register(Bitrix24CreateTaskIntegration())
