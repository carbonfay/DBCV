"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

# AmoCRM интеграции
try:
    from app.integrations.amocrm import *  # noqa: F401, F403
except ImportError:
    # Библиотека или регистрация интеграций не установлена, пропускаем
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
