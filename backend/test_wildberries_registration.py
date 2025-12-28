"""Скрипт для проверки регистрации Wildberries интеграции."""
import sys
from pathlib import Path

# Добавляем путь к app в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "app"))

try:
    from app.integrations.registry import registry
    
    # Получаем интеграцию
    wb_integration = registry.get("wildberries_update_stock")
    
    if wb_integration:
        print("✅ Интеграция Wildberries успешно зарегистрирована!")
        print(f"\nМетаданные:")
        metadata = wb_integration.metadata
        print(f"  ID: {metadata.id}")
        print(f"  Версия: {metadata.version}")
        print(f"  Название: {metadata.name}")
        print(f"  Описание: {metadata.description}")
        print(f"  Категория: {metadata.category}")
        print(f"  Провайдер credentials: {metadata.credentials_provider}")
        print(f"  Стратегия: {metadata.credentials_strategy}")
        print(f"  Библиотека: {metadata.library_name}")
        
        print(f"\n📋 Все зарегистрированные интеграции:")
        for meta in registry.list_all():
            print(f"  - {meta.id} v{meta.version} ({meta.category})")
    else:
        print("❌ Интеграция Wildberries НЕ найдена в реестре!")
        print(f"\nДоступные интеграции:")
        for meta in registry.list_all():
            print(f"  - {meta.id} v{meta.version}")
            
except Exception as e:
    print(f"❌ Ошибка при проверке: {e}")
    import traceback
    traceback.print_exc()
</contents>