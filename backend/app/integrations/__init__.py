"""Интеграции с внешними сервисами.

При импорте пакета выполняется явная регистрация интеграций через
функции `register_all()` в подпакетах. Такой подход уменьшает побочные
эффекты импорта и упрощает тестирование.
"""
try:
    # Попытка импортировать и зарегистрировать интеграции Telegram.
    from app.integrations import telegram

    try:
        telegram.register_all()
    except Exception:
        # Если регистрация не удалась (например, отсутствуют зависимости), пропускаем
        pass
except ImportError:
    # Пакет telegram отсутствует — продолжаем
    pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import *  # noqa: F401, F403
