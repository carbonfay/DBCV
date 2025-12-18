# Интеграции с внешними сервисами

# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотек нет установленных, пропускаем
    pass

try:
    from app.integrations.github import *  # noqa: F401, F403
except ImportError:
    pass

try:
    from app.integrations.yookassa import *  # noqa: F401, F403
except ImportError:
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
