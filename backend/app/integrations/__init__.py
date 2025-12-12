"""Интеграции с внешними сервисами."""

# --- TELEGRAM ---
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    pass

# --- VK ---
from app.integrations.vk import *

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
