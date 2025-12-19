"""Интеграции с внешними сервисами."""
# Автоматическая регистрация интеграций при импорте
try:
    from app.integrations.telegram import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.discord import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.google import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.classroom import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.stripe import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.paypal import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.moodle import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.vk import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.hubspot import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.weather import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.maps import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.crm import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.storage import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.yookassa import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

try:
    from app.integrations.ai import *  # noqa: F401, F403
except ImportError:
    # Библиотека не установлена, пропускаем
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
