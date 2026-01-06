"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте

# Telegram
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    pass

# Ozon (ВОТ ЭТО МЫ ДОБАВЛЯЕМ)
try:
    from app.integrations.ozon import *  # noqa: F401, F403
except ImportError:
    pass

try:
    from app.integrations.moodle import * 
except ImportError:
    pass
# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403