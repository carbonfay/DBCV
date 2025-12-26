"""Тест интеграции Wildberries БЕЗ подключения к БД."""
import sys
from pathlib import Path

# Добавляем путь к app в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🧪 Wildberries Integration Test (No DB)")
print("=" * 60)
print()

try:
    # Проверяем импорт самой интеграции напрямую
    print("1. Импорт класса интеграции...")
    from app.integrations.Wildberries.update_stock import WildberriesUpdateStockIntegration
    print("   ✅ Класс импортирован")
    
    print("\n2. Создание экземпляра интеграции...")
    integration = WildberriesUpdateStockIntegration()
    print("   ✅ Экземпляр создан")
    
    print("\n3. Получение метаданных...")
    metadata = integration.metadata
    print(f"   ✅ Метаданные получены")
    
    print(f"\n📋 Информация об интеграции:")
    print(f"   ID: {metadata.id}")
    print(f"   Версия: {metadata.version}")
    print(f"   Название: {metadata.name}")
    print(f"   Описание: {metadata.description}")
    print(f"   Категория: {metadata.category}")
    print(f"   Провайдер: {metadata.credentials_provider}")
    print(f"   Стратегия: {metadata.credentials_strategy}")
    
    print(f"\n⚙️ Схема конфигурации:")
    import json
    print(json.dumps(metadata.config_schema, indent=2, ensure_ascii=False))
    
    print(f"\n💡 Примеры:")
    for i, example in enumerate(metadata.examples, 1):
        print(f"   {i}. {example['title']}")
        print(f"      Config: {json.dumps(example['config'], ensure_ascii=False)}")
    
    print("\n4. Проверка библиотеки wildberries_api...")
    try:
        import wildberries_api
        print("   ✅ wildberries_api установлена")
        print(f"   Версия: {getattr(wildberries_api, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"   ⚠️  wildberries_api НЕ установлена")
        print(f"   Причина: {e}")
        print(f"   Интеграция вернет ошибку при выполнении")
    
    print("\n✅ Базовый тест пройден!")
    print("\nДля запуска с реальными данными нужно:")
    print("1. Установить библиотеку: pip install wildberries-api")
    print("2. Настроить базу данных")
    print("3. Добавить credentials для Wildberries")
    print("4. Запустить: python run_wildberries_integration.py")

except ImportError as e:
    print(f"\n❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
</contents>