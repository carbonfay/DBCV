"""Интеграции с внешними сервисами."""
"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте — импортируем конкретные
# модули интеграций (подмодули), чтобы их код мог зарегистрировать себя.
try:
    import importlib
    # Messaging
    importlib.import_module('app.integrations.telegram.send_message')
    # Medicine
    importlib.import_module('app.integrations.medicine.search_drugs')
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

# Внутренние интеграции DBCV (оставляем как есть)
from app.integrations.dbcv import *  # noqa: F401, F403
