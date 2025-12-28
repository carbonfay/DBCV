"""Скрипт для запуска интеграции Wildberries Update Stock."""
import sys
import asyncio
from pathlib import Path
from uuid import UUID

# Добавляем путь к app в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from app.integrations.registry import registry
from app.auth.credentials_resolver import CredentialsResolver
from app.managers.data_manager import DataManager
from app.loggers.bot import BotLogger
from app.database import sessionmanager


async def run_wildberries_integration():
    """Запускает интеграцию Wildberries для обновления остатков."""
    
    # Инициализация базы данных
    sessionmanager.init()
    
    try:
        # Получаем интеграцию из реестра
        wb_integration = registry.get("wildberries_update_stock")
        
        if not wb_integration:
            print("❌ Интеграция Wildberries не найдена в реестре!")
            return
        
        print("✅ Интеграция найдена:")
        print(f"   ID: {wb_integration.metadata.id}")
        print(f"   Название: {wb_integration.metadata.name}")
        print(f"   Версия: {wb_integration.metadata.version}")
        print()
        
        # Настройки для выполнения (замените на свои значения)
        BOT_ID = input("Введите BOT_ID (UUID): ").strip()
        SKU = input("Введите SKU товара: ").strip()
        STOCK = input("Введите количество на складе: ").strip()
        WAREHOUSE_ID = input("Введите ID склада (или оставьте пустым): ").strip()
        
        try:
            bot_id = UUID(BOT_ID)
            stock = int(STOCK)
        except ValueError as e:
            print(f"❌ Ошибка в данных: {e}")
            return
        
        # Конфигурация интеграции
        config = {
            "sku": SKU,
            "stock": stock,
        }
        
        if WAREHOUSE_ID:
            config["warehouse_id"] = WAREHOUSE_ID
        
        print(f"\n📋 Конфигурация:")
        print(f"   SKU: {config['sku']}")
        print(f"   Stock: {config['stock']}")
        if 'warehouse_id' in config:
            print(f"   Warehouse ID: {config['warehouse_id']}")
        print()
        
        # Создаем DataManager и CredentialsResolver
        data_manager = DataManager()
        credentials_resolver = CredentialsResolver(data_manager)
        
        # Создаем логгер (простой вывод в консоль)
        class ConsoleLogger(BotLogger):
            """Простой логгер для вывода в консоль."""
            
            def __init__(self):
                # Не вызываем __init__ родителя, так как он требует bot_id
                pass
            
            async def debug(self, message: str, **kwargs):
                print(f"[DEBUG] {message}")
            
            async def info(self, message: str, **kwargs):
                print(f"[INFO] {message}")
            
            async def warning(self, message: str, **kwargs):
                print(f"[WARNING] {message}")
            
            async def error(self, message: str, **kwargs):
                print(f"[ERROR] {message}")
            
            async def critical(self, message: str, **kwargs):
                print(f"[CRITICAL] {message}")
        
        logger = ConsoleLogger()
        
        print("🚀 Запуск интеграции...\n")
        
        # Выполняем интеграцию
        result = await wb_integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )
        
        print(f"\n📊 Результат выполнения:")
        print(f"   OK: {result.get('response', {}).get('ok', False)}")
        
        if result.get('response', {}).get('ok'):
            print(f"   ✅ Остатки успешно обновлены!")
            if result.get('response', {}).get('result'):
                print(f"   Результат: {result['response']['result']}")
        else:
            print(f"   ❌ Ошибка при выполнении:")
            print(f"   Код ошибки: {result.get('response', {}).get('error_code')}")
            print(f"   Описание: {result.get('response', {}).get('description')}")
            if result.get('response', {}).get('error'):
                print(f"   Детали: {result['response']['error']}")
    
    except KeyboardInterrupt:
        print("\n⚠️ Выполнение прервано пользователем")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем соединение с БД
        if sessionmanager.engine is not None:
            await sessionmanager.close()
        print("\n✅ Соединения закрыты")


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Wildberries Update Stock Integration Runner")
    print("=" * 60)
    print()
    
    asyncio.run(run_wildberries_integration())
</contents>