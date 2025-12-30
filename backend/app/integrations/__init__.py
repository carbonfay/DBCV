"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *
except ImportError:
    pass

try:
    from app.integrations.github import *
except ImportError:
    pass

from app.integrations.dbcv import *