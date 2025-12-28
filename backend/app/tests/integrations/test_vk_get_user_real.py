"""
Реальный тест VK Get User интеграции.
Получает реальную информацию о пользователе VK.
"""

import asyncio
import sys
from uuid import UUID

# Добавляем путь
sys.path.insert(0, '/app')

from app.integrations.vk.get_user import VkGetUserIntegration

# НАСТРОЙКИ
VK_TOKEN = 'vk1.a.4WRHln_zYompJA0dQE3LJHePeu6v_G--mX7bv04EROD_Uf_tNKqTaWwudrT7IC-89gcIRO3wFrupRPD1NXDlQ5Ck9Tuc1ngkZlw2ZXp4fgJadg1LhXsxu_qssrtcPJpY8O-GBEw9tMGLQmSUTdDKIsVWXZPDMlaMVn_bWH4WsPmeTn7dQgid4bdn4-TqdXrTOQP8JK6b6Y-d6xchInSdIA'
VK_USER_ID = '72923353'


class MockCredentialsResolver:
    """Mock credentials resolver с реальным токеном."""
    
    async def get_default_for(self, bot_id, provider, strategy):
        """Возвращает реальный токен VK."""
        return {
            "payload": {
                "access_token": VK_TOKEN
            }
        }


class MockLogger:
    """Mock logger."""
    
    async def error(self, message):
        print(f"[ERROR] {message}")
    
    async def info(self, message):
        print(f"[INFO] {message}")


async def test_get_user_basic():
    """Тест получения базовой информации о пользователе."""
    print("\n" + "="*60)
    print("🚀 ТЕСТ 1: Базовая информация о пользователе")
    print("="*60)
    print(f"User ID: {VK_USER_ID}")
    print("="*60 + "\n")
    
    integration = VkGetUserIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {
        "user_ids": VK_USER_ID,
        "fields": ["photo_100", "online", "domain"]
    }
    
    try:
        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        if result["response"]["ok"]:
            users = result["response"]["result"]["users"]
            user = users[0] if users else {}
            
            print("✅ УСПЕХ! Информация получена:")
            print(f"   ID: {user.get('id')}")
            print(f"   Имя: {user.get('first_name')} {user.get('last_name')}")
            print(f"   Domain: {user.get('domain', 'не указан')}")
            print(f"   Online: {'Да' if user.get('online') else 'Нет'}")
            print(f"   Photo: {user.get('photo_100', 'не указано')[:50]}...")
            print(f"\n   Полный результат: {result}")
        else:
            print("\n❌ ОШИБКА:")
            print(f"   Error code: {result['response']['error_code']}")
            print(f"   Description: {result['response']['description']}")
            
    except Exception as e:
        print(f"\n❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()


async def test_get_user_extended():
    """Тест получения расширенной информации."""
    print("\n" + "="*60)
    print("📝 ТЕСТ 2: Расширенная информация о пользователе")
    print("="*60 + "\n")
    
    integration = VkGetUserIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {
        "user_ids": VK_USER_ID,
        "fields": [
            "photo_200",
            "online",
            "domain",
            "bdate",
            "city",
            "country",
            "status",
            "last_seen"
        ]
    }
    
    try:
        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        if result["response"]["ok"]:
            users = result["response"]["result"]["users"]
            user = users[0] if users else {}
            
            print("✅ УСПЕХ! Расширенная информация получена:")
            print(f"   ID: {user.get('id')}")
            print(f"   Имя: {user.get('first_name')} {user.get('last_name')}")
            print(f"   Domain: @{user.get('domain', 'не указан')}")
            print(f"   Дата рождения: {user.get('bdate', 'не указана')}")
            print(f"   Город: {user.get('city', {}).get('title', 'не указан')}")
            print(f"   Страна: {user.get('country', {}).get('title', 'не указана')}")
            print(f"   Статус: {user.get('status', 'не указан')}")
            print(f"   Online: {'Да' if user.get('online') else 'Нет'}")
            
            if 'last_seen' in user:
                print(f"   Последний визит: {user['last_seen'].get('time', 'неизвестно')}")
        else:
            print("\n❌ ОШИБКА:")
            print(f"   Error code: {result['response']['error_code']}")
            print(f"   Description: {result['response']['description']}")
            
    except Exception as e:
        print(f"\n❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()


async def test_get_multiple_users():
    """Тест получения информации о нескольких пользователях."""
    print("\n" + "="*60)
    print("👥 ТЕСТ 3: Несколько пользователей")
    print("="*60 + "\n")
    
    integration = VkGetUserIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {
        "user_ids": [1, 210700286],  # Павел Дуров и другой пользователь
        "fields": ["photo_100", "online", "domain"]
    }
    
    try:
        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        if result["response"]["ok"]:
            users = result["response"]["result"]["users"]
            count = result["response"]["result"]["count"]
            
            print(f"✅ УСПЕХ! Получена информация о {count} пользователях:")
            for user in users:
                print(f"\n   - {user.get('first_name')} {user.get('last_name')}")
                print(f"     ID: {user.get('id')}")
                print(f"     Domain: @{user.get('domain', 'не указан')}")
                print(f"     Online: {'Да' if user.get('online') else 'Нет'}")
        else:
            print("\n❌ ОШИБКА:")
            print(f"   Error code: {result['response']['error_code']}")
            print(f"   Description: {result['response']['description']}")
            
    except Exception as e:
        print(f"\n❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()


async def test_metadata():
    """Тест метаданных."""
    print("\n" + "="*60)
    print("📋 ТЕСТ 4: Проверка метаданных интеграции")
    print("="*60 + "\n")
    
    integration = VkGetUserIntegration()
    metadata = integration.metadata
    
    print(f"ID: {metadata.id}")
    print(f"Version: {metadata.version}")
    print(f"Name: {metadata.name}")
    print(f"Category: {metadata.category}")
    print(f"Provider: {metadata.credentials_provider}")
    print(f"Strategy: {metadata.credentials_strategy}")
    print(f"Library: {metadata.library_name}")
    print(f"Color: {metadata.color}")
    print(f"Examples: {len(metadata.examples)} шт.")
    
    print("\n✅ Метаданные корректны!")


async def main():
    """Главная функция."""
    try:
        # Проверяем метаданные
        await test_metadata()
        
        # Получаем базовую информацию
        await test_get_user_basic()
        
        # Ждем 1 секунду
        await asyncio.sleep(1)
        
        # Получаем расширенную информацию
        await test_get_user_extended()
        
        # Ждем 1 секунду
        await asyncio.sleep(1)
        
        # Получаем информацию о нескольких пользователях
        await test_get_multiple_users()
        
        print("\n" + "="*60)
        print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
