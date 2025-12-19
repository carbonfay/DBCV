"""Bitrix24 интеграции: импорт и регистрация всех реализаций."""
from .update_deal import Bitrix24UpdateDealIntegration

from app.integrations.registry import registry


registry.register(Bitrix24UpdateDealIntegration())
