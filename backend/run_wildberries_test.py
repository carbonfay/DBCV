"""Простой скрипт для быстрого тестирования Wildberries интеграции."""
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Добавляем путь к app в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from app.integrations.registry import registry

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def print_section(title: str, char: str = "=") -> None:
    """Выводит форматированный заголовок секции."""
    print()
    print(char * 60)
    print(f"{title}")
    print(char * 60)
    print()


def print_metadata(metadata: Dict[str, Any]) -> None:
    """Выводит метаданные интеграции в структурированном виде."""
    import json
    
    print("📋 Метаданные интеграции:")
    print(f"   ID: {metadata.id}")
    print(f"   Версия: {metadata.version}")
    print(f"   Название: {metadata.name}")
    print(f"   Описание: {metadata.description}")
    print(f"   Категория: {metadata.category}")
    print(f"   Цвет: {metadata.color}")
    print(f"   Иконка: {metadata.icon_s3_key}")
    print()
    
    print("🔐 Настройки аутентификации:")
    print(f"   Провайдер: {metadata.credentials_provider}")
    print(f"   Стратегия: {metadata.credentials_strategy}")
    print()
    
    print("📦 Библиотека:")
    print(f"   {metadata.library_name}")
    print()
    
    print("⚙️ Схема конфигурации:")
    print(json.dumps(metadata.config_schema, indent=2, ensure_ascii=False))
    print()
    
    if metadata.examples:
        print("💡 Примеры использования:")
        for i, example in enumerate(metadata.examples, 1):
            print(f"   Пример {i}: {example['title']}")
            print(f"   Config: {json.dumps(example['config'], ensure_ascii=False)}")
        print()


async def test_integration() -> bool:
    """Тестирует интеграцию Wildberries без выполнения.
    
    Returns:
        bool: True если тест успешен, False в противном случае
    """
    try:
        print_section("🧪 Wildberries Integration Test (Registry Check)")
        
        logger.info("Начало проверки регистрации интеграции Wildberries")
    
        # Получаем интеграцию
        wb_integration = registry.get("wildberries_update_stock")
        
        if wb_integration:
            logger.info("Интеграция Wildberries найдена в реестре")
            print("✅ Интеграция Wildberries успешно зарегистрирована!\n")
            
            metadata = wb_integration.metadata
            print_metadata(metadata)
            
            print("📊 Все зарегистрированные интеграции:")
            all_integrations = registry.list_all()
            logger.info(f"Найдено интеграций в реестре: {len(all_integrations)}")
            
            for meta in all_integrations:
                status = "✓" if meta.id == "wildberries_update_stock" else "○"
                print(f"   {status} {meta.id} v{meta.version} ({meta.category})")
            print()
            
            print("✅ Интеграция готова к использованию!")
            print()
            print("Для запуска интеграции с реальными данными используйте:")
            print("   python run_wildberries_integration.py")
            print("   или")
            print("   .\\run_wildberries.ps1  (для полной интеграции с параметрами)")
            
            logger.info("Проверка интеграции завершена успешно")
            return True
            
        else:
            logger.error("Интеграция Wildberries не найдена в реестре")
            print("❌ Интеграция Wildberries НЕ найдена в реестре!\n")
            
            print("Доступные интеграции:")
            all_integrations = registry.list_all()
            if all_integrations:
                for meta in all_integrations:
                    print(f"   - {meta.id} v{meta.version}")
            else:
                print("   (реестр пуст)")
            
            return False
    
    except Exception as e:
        logger.exception(f"Ошибка при проверке интеграции: {e}")
        print(f"\n❌ Произошла ошибка: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_integration())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("Проверка прервана пользователем")
        print("\n⚠️ Проверка прервана пользователем")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
```