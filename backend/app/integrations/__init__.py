"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

# Внутренние интеграции DBCV
try:
    from app.integrations.amocrm import *  # noqa: F401, F403
except ImportError:
    pass

from app.integrations.dbcv import *  # noqa: F401, F403
