"""Yandex Maps интеграции."""
from .suggest import YandexMapsSuggestIntegration
from app.integrations.registry import registry

# Регистрируем интеграцию
registry.register(YandexMapsSuggestIntegration())

__all__ = ["YandexMapsSuggestIntegration"]