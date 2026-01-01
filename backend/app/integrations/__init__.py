"""Интеграции с внешними сервисами.
Автоматически импортируем подмодули и их модули, чтобы вызвался код
регистрации интеграций при импорте пакета.
"""
import importlib
import pkgutil
import os

package_dir = os.path.dirname(__file__)
for _finder, pkg_name, ispkg in pkgutil.iter_modules([package_dir]):
    try:
        importlib.import_module(f"app.integrations.{pkg_name}")
    except Exception:
        continue

    subdir = os.path.join(package_dir, pkg_name)
    if os.path.isdir(subdir):
        for _mfinder, mod_name, _ in pkgutil.iter_modules([subdir]):
            try:
                importlib.import_module(f"app.integrations.{pkg_name}.{mod_name}")
            except Exception:
                pass

# Внутренние интеграции DBCV
from app.integrations.dbcv import * # noqa: F401, F403