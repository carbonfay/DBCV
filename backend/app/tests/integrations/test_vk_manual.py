"""
Скрипт для ручного тестирования VK Send Message интеграции.

Использование:
1. Установите vk-api: pip install vk-api>=11.9.9
2. Установите переменные окружения или замените значения в коде:
   - VK_ACCESS_TOKEN: токен доступа VK
   - VK_USER_ID: ID пользователя VK для отправки тестового сообщения
3. Запустите: python test_vk_manual.py
"""

import asyncio
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock

# Добавляем путь для импорта модулей приложения
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.integrations.vk.send_message import VkSendMessageIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


# НАСТРОЙКИ - ЗАМЕНИТЕ НА СВОИ ЗНАЧЕНИЯ
VK_ACCESS_TOKEN = "your_vk_access_token_here"  # Токен VK группы или пользователя
VK_USER_ID = "123456789"  # ID пользователя для тестовой отправки


class MockCredentialsResolver:
    """Mock credentials resolver для тестирования."""
    
    async def get_default_for(self, bot_id, provider, strategy):
        """Возвращает тестовые credentials."""
        return {
            "payload": {
                "access_token": VK_ACCESS_TOKEN
            }
        }


class MockLogger:
    """Mock logger для тестирования."""
    
    async def error(self, message):
        print(f"[ERROR] {message}")
    
    async def info(self, message):
        print(f"[INFO] {message}")


async def test_simple_message():
    """Тест отправки простого сообщения."""
    print("\n" + "="*60)
    print("ТЕСТ 1: Простое сообщение")
    print("="*60)
    
    integration = VkSendMessageIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {
        "user_id": VK_USER_ID,
        "message": "🚀 Тестовое сообщение из DBCV!"
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    print(f"\nРезультат: {result}")
    
    if result["response"]["ok"]:
        print("✅ ТЕСТ ПРОЙДЕН: Сообщение отправлено успешно!")
        print(f"   Message ID: {result['response']['result']['message_id']}")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН:")
        print(f"   Error code: {result['response']['error_code']}")
        print(f"   Description: {result['response']['description']}")


async def test_message_with_keyboard():
    """Тест отправки сообщения с клавиатурой."""
    print("\n" + "="*60)
    print("ТЕСТ 2: Сообщение с клавиатурой")
    print("="*60)
    
    integration = VkSendMessageIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {
        "user_id": VK_USER_ID,
        "message": "Выберите опцию:",
        "keyboard": {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "✅ Да"
                        },
                        "color": "positive"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "❌ Нет"
                        },
                        "color": "negative"
                    }
                ]
            ]
        }
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    print(f"\nРезультат: {result}")
    
    if result["response"]["ok"]:
        print("✅ ТЕСТ ПРОЙДЕН: Сообщение с клавиатурой отправлено!")
        print(f"   Message ID: {result['response']['result']['message_id']}")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН:")
        print(f"   Error code: {result['response']['error_code']}")
        print(f"   Description: {result['response']['description']}")


async def test_invalid_credentials():
    """Тест с неверными credentials."""
    print("\n" + "="*60)
    print("ТЕСТ 3: Неверные credentials (ожидается ошибка)")
    print("="*60)
    
    integration = VkSendMessageIntegration()
    
    # Mock resolver без credentials
    class EmptyResolver:
        async def get_default_for(self, bot_id, provider, strategy):
            return None
    
    credentials_resolver = EmptyResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {
        "user_id": VK_USER_ID,
        "message": "Test"
    }
    
    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    print(f"\nРезультат: {result}")
    
    if not result["response"]["ok"] and result["response"]["error_code"] == 401:
        print("✅ ТЕСТ ПРОЙДЕН: Ошибка обработана корректно!")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН: Ожидалась ошибка 401")


async def test_missing_parameters():
    """Тест с отсутствующими параметрами."""
    print("\n" + "="*60)
    print("ТЕСТ 4: Отсутствующие параметры (ожидается ошибка)")
    print("="*60)
    
    integration = VkSendMessageIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {}  # Нет обязательных параметров
    
    result = await integration.execute(
        config=config,
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    print(f"\nРезультат: {result}")
    
    if not result["response"]["ok"] and result["response"]["error_code"] == 400:
        print("✅ ТЕСТ ПРОЙДЕН: Валидация параметров работает!")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН: Ожидалась ошибка 400")


async def test_metadata():
    """Тест метаданных интеграции."""
    print("\n" + "="*60)
    print("ТЕСТ 5: Проверка метаданных")
    print("="*60)
    
    integration = VkSendMessageIntegration()
    metadata = integration.metadata
    
    checks = [
        ("ID", metadata.id == "vk_send_message"),
        ("Version", metadata.version == "1.0.0"),
        ("Name", metadata.name == "VK Send Message"),
        ("Category", metadata.category == "messaging"),
        ("Provider", metadata.credentials_provider == "vk"),
        ("Strategy", metadata.credentials_strategy == "api_key"),
        ("Config schema exists", metadata.config_schema is not None),
        ("Examples exist", metadata.examples is not None and len(metadata.examples) > 0),
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {result}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✅ ВСЕ ПРОВЕРКИ МЕТАДАННЫХ ПРОЙДЕНЫ!")
    else:
        print("\n❌ НЕКОТОРЫЕ ПРОВЕРКИ ПРОВАЛЕНЫ!")


async def main():
    """Главная функция - запускает все тесты."""
    print("\n" + "="*60)
    print("VK SEND MESSAGE INTEGRATION - РУЧНОЕ ТЕСТИРОВАНИЕ")
    print("="*60)
    
    # Проверка настроек
    if VK_ACCESS_TOKEN == "your_vk_access_token_here":
        print("\n⚠️  ВНИМАНИЕ: Необходимо указать VK_ACCESS_TOKEN в коде!")
        print("   Тесты с реальной отправкой будут пропущены.")
        
        # Запускаем только тесты без отправки
        await test_metadata()
        await test_invalid_credentials()
        await test_missing_parameters()
    else:
        # Запускаем все тесты
        await test_metadata()
        await test_invalid_credentials()
        await test_missing_parameters()
        await test_simple_message()
        await test_message_with_keyboard()
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
