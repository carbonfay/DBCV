"""Регистрация Yandex интеграций."""
from .translate_detect import YandexTranslateDetectIntegration
from app.integrations.registry import registry

# Регистрируем Yandex интеграции
try:
    registry.register(YandexTranslateDetectIntegration())
except Exception as e:
    import logging