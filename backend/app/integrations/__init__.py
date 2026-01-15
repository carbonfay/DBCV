"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаемаа
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403

# Интеграции, расположенные в подпакете medicine
try:
    from app.integrations.medicine import *  # noqa: F401, F403
except ImportError:
    # Не критично, продолжаем работу без medicine-интеграций
    pass
