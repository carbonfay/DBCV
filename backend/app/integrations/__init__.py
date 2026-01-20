"""Интеграции с внешними сервисами."""

# Внутренние интеграции DBCV (всегда сверху)
from app.integrations.dbcv import * # noqa: F401, F403

# Подключаем твою папку medicine напрямую
import logging
logger = logging.getLogger(__name__)
try:
    from . import medicine
except Exception as e:
    # Если здесь ошибка, сервер не упадет, но напишет в чем дело
    logger.exception("Error loading medicine package")

# Telegram (если есть)
try:
    from app.integrations.telegram import * # noqa: F401, F403
except ImportError:
    pass