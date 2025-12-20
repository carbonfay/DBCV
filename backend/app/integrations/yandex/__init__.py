"""Регистрация Yandex интеграций."""
from .translate_translate import YandexTranslateTranslateIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(YandexTranslateTranslateIntegration())