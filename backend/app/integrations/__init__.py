"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

# Bitrix24 интеграции (опционально импортируем, чтобы регистрация сработала)
try:
    from app.integrations.bitrix24 import *  # noqa: F401, F403
except ImportError:
    # Если пакет битрикс не доступен на этапе импорта — пропускаем
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
