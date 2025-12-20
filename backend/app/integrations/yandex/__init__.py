"""Регистрация Yandex интеграций."""
from .translate_languages import YandexTranslateLanguagesIntegration
from app.integrations.registry import registry

# Регистрируем Yandex Translate Languages интеграцию
registry.register(YandexTranslateLanguagesIntegration())