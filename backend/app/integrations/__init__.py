"""Интеграции с внешними сервисами."""

# --- TELEGRAM ---
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    pass

# --- VK ---
try:
    from app.integrations.vk_shinkevichOVKIPo_301 import *
except ImportError:
    pass


# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
