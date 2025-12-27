"""Простой тест интеграции Wildberries без инициализации БД."""
import sys
from pathlib import Path

# Добавляем путь к app в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🧪 Wildberries Integration Simple Test")
print("=" * 60)
print()

try:
    print("1. Импорт registry...")
    from app.integrations.registry import registry
    print("   ✅ Registry imported successfully")
    
    print("\n2. Получение интеграции Wildberries...")
    wb_integration = registry.get("wildberries_update_stock")
    
    if wb_integration:
        print("   ✅ Интеграция найдена!")
        print(f"\n   ID: {wb_integration.metadata.id}")
        print(f"   Версия: {wb_integration.metadata.version}")
        print(f"   Название: {wb_integration.metadata.name}")
        print(f"   Описание: {wb_integration.metadata.description}")
        print(f"   Категория: {wb_integration.metadata.category}")
        
        print("\n3. Проверка библиотеки wildberries_api...")
        try:
            import wildberries_api
            print("   ✅ wildberries_api установлена")
        except ImportError:
            print("   ⚠️  wildberries_api НЕ установлена (будет использоваться заглушка)")
        
        print("\n4. Все зарегистрированные интеграции:")
        for meta in registry.list_all():
            status = "✓" if meta.id == "wildberries_update_stock" else "○"
            print(f"   {status} {meta.id} v{meta.version} ({meta.category})")
        
        print("\n✅ Тест пройден успешно!")
        print("\nДля запуска полной интеграции используйте:")
        print("   python run_wildberries_integration.py")
    else:
        print("   ❌ Интеграция НЕ найдена!")
        print("\n   Доступные интеграции:")
        for meta in registry.list_all():
            print(f"      - {meta.id} v{meta.version}")

except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
</contents>