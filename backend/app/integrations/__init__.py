"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаемаа
    pass

# Интеграции, которые расположены в подпакете medicine
try:
    from app.integrations.medicine import *  # noqa: F401, F403
except ImportError:
    # Не обязательно установленны внешние зависимости — пропускаем
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
