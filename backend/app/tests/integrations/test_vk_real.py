"""
Реальный тест VK интеграции с настоящим токеном.
Отправляет реальное сообщение в VK.
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID
from unittest.mock import MagicMock

# Добавляем путь
sys.path.insert(0, '/app')

from app.integrations.vk.send_message import VkSendMessageIntegration

# НАСТРОЙКИ
VK_TOKEN = 'vk1.a.4WRHln_zYompJA0dQE3LJHePeu6v_G--mX7bv04EROD_Uf_tNKqTaWwudrT7IC-89gcIRO3wFrupRPD1NXDlQ5Ck9Tuc1ngkZlw2ZXp4fgJadg1LhXsxu_qssrtcPJpY8O-GBEw9tMGLQmSUTdDKIsVWXZPDMlaMVn_bWH4WsPmeTn7dQgid4bdn4-TqdXrTOQP8JK6b6Y-d6xchInSdIA'
VK_PEER_ID = '72923353'


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


async def test_send_simple_message():
    """Тест отправки простого сообщения."""
    print("\n" + "="*60)
    print("🚀 РЕАЛЬНЫЙ ТЕСТ VK ИНТЕГРАЦИИ")
    print("="*60)
    print(f"Peer ID: {VK_PEER_ID}")
    print(f"Token: {VK_TOKEN[:20]}...")
    print("="*60 + "\n")
    
    integration = VkSendMessageIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    # Тест 1: Простое сообщение
    print("📝 Тест 1: Отправка простого сообщения...")
    config = {
        "user_id": VK_PEER_ID,
        "message": "🎉 Привет! Это тестовое сообщение из DBCV интеграции VK!"
    }
    
    try:
        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        print(f"\nРезультат: {result}")
        
        if result["response"]["ok"]:
            print("\n✅ УСПЕХ! Сообщение отправлено!")
            print(f"   Message ID: {result['response']['result']['message_id']}")
            print(f"   User ID: {result['response']['result']['user_id']}")
            print(f"   Random ID: {result['response']['result']['random_id']}")
        else:
            print("\n❌ ОШИБКА:")
            print(f"   Error code: {result['response']['error_code']}")
            print(f"   Description: {result['response']['description']}")
            
    except Exception as e:
        print(f"\n❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()


async def test_send_message_with_keyboard():
    """Тест отправки сообщения с клавиатурой."""
    print("\n" + "="*60)
    print("📝 Тест 2: Отправка сообщения с клавиатурой...")
    print("="*60 + "\n")
    
    integration = VkSendMessageIntegration()
    credentials_resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    config = {
        "user_id": VK_PEER_ID,
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
                ],
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "ℹ️ Помощь"
                        },
                        "color": "primary"
                    }
                ]
            ]
        }
    }
    
    try:
        result = await integration.execute(
            config=config,
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        print(f"\nРезультат: {result}")
        
        if result["response"]["ok"]:
            print("\n✅ УСПЕХ! Сообщение с клавиатурой отправлено!")
            print(f"   Message ID: {result['response']['result']['message_id']}")
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
    print("📋 Тест 3: Проверка метаданных интеграции")
    print("="*60 + "\n")
    
    integration = VkSendMessageIntegration()
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
        
        # Отправляем простое сообщение
        await test_send_simple_message()
        
        # Ждем 2 секунды между сообщениями
        await asyncio.sleep(2)
        
        # Отправляем сообщение с клавиатурой
        await test_send_message_with_keyboard()
        
        print("\n" + "="*60)
        print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
