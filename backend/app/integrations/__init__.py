"""Интеграции с внешними сервисами.

Вместо явного перечисления модулей делаем рекурсивный импорт всех
подмодулей внутри пакета `app.integrations` — это устойчиво к
добавлению новых подпакетов (например `medicine`).
"""
import importlib
import pkgutil


def _import_all_integrations():
    pkg = importlib.import_module(__name__)
    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            importlib.import_module(name)
        except Exception:
            # Не прерываем стартап из-за одной неработающей интеграции
            # — она просто не зарегистрируется в реестре.
            pass


# Запускаем динамический импорт
_import_all_integrations()

# Внутренние интеграции DBCV (оставляем без изменений)
from app.integrations.dbcv import *  # noqa: F401, F403