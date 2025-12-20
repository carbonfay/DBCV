"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass


#import bitrix24 integrations
try:
    from app.integrations.bitrix24 import *  # noqa: F401, F403
except ImportError:
    pass


# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403

