"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass
# YooKassa интеграции
try:
    from app.integrations.yookassa import *  # noqa: F401, F403
except ImportError:
    pass
# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
from app.integrations.yookassa_refund import YookassaRefundIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграции YooKassa Refund
registry.register(YookassaRefundIntegration())
