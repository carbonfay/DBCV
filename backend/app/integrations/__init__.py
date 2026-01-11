"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403

# Экспортируем основные классы и реестр
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.integrations.registry import registry, IntegrationRegistry

__all__ = [
    "BaseIntegration",
    "IntegrationMetadata",
    "registry",
    "IntegrationRegistry",
]