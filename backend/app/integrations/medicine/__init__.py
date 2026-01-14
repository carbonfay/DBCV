"""Пакет интеграций для работы с фармацевтическими данными."""
# Ничего сложного: при импорте подпакета все модули внутри зарегистрируют свои интеграции
from .get_drug_info import *  # noqa: F401, F403
"""
Medicine integrations package.
Автоматическая регистрация всех модулей в этой директории.
"""
import importlib
import pkgutil

def _import_all_integrations():
    """
    Рекурсивно импортирует все подмодули в текущем пакете,
    чтобы сработал декоратор/метод регистрации внутри них.
    """
    try:
        # Получаем текущий пакет
        pkg = importlib.import_module(__name__)
        
        # Проходимся по всем файлам в папке
        for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            try:
                importlib.import_module(name)
            except Exception as e:
                # Логируем ошибку, но не роняем сервер
                print(f"Failed to auto-import medicine integration {name}: {e}")
                pass
    except Exception as e:
        print(f"Error in medicine package initialization: {e}")

# Запускаем динамический импорт при старте
_import_all_integrations()

from .get_drug_info import MedicineGetDrugInfoIntegration
from app.integrations.registry import registry

# Явная регистрация интеграций в пакете (как в других интеграциях)
try:
    registry.register(MedicineGetDrugInfoIntegration())
except Exception as e:
    print(f"Failed to register medicine integration: {e}")

__all__ = ["MedicineGetDrugInfoIntegration"]