"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

# Попытка импортировать GitHub-интеграции для автоматической регистрации
try:
    from app.integrations.github import *  # noqa: F401, F403
except ImportError:
    # PyGithub или пакет интеграций не установлен/недоступен — пропускаем
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
