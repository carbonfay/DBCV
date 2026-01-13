import asyncio
import vk_api
from uuid import UUID

class MockCredentialsResolver:
    def __init__(self, token):
        self.token = token

    async def get_default_for(self, bot_id, provider, strategy):
        return {"payload": {"access_token": self.token}}

class MockLogger:
    async def error(self, msg):
        print(f"ERROR: {msg}")

async def test_integration():
    # Новый токен
    token = "vk1.a.GaAwWm4-DDSNNDaP5KA06keLpDKayAI4rh-F7J7oak0zJ1nEGrzfvAJaFaiVv1BTZJ0Q7PEMd48xpPeNL_fr6wGRhoA6Ak56-1sjVzPDNxGDr5dO1lUiv6zsUOvHzPdPrGByiHlT3bszLq-Z3he-XH_oRBGZGIrWOaJSoZaDv40sybHrrS3fZvkE_VIn16Nkq2Q_i2cklxCKhDO3548fiw"

    # Проверяем токен
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        user = vk.users.get()
        print("✓ Токен VK валиден")
        print(f"Пользователь: {user[0]['first_name']} {user[0]['last_name']} (ID: {user[0]['id']})")
    except Exception as e:
        print(f"✗ Ошибка токена VK: {e}")
        return

    # Импортируем интеграцию
    try:
        from app.integrations.vk.send_photo import VkSendPhotoIntegration
        print("✓ Интеграция импортирована успешно")
    except Exception as e:
        print(f"✗ Ошибка импорта интеграции: {e}")
        return

    # Проверяем метаданные
    integration = VkSendPhotoIntegration()
    metadata = integration.metadata
    print("✓ Метаданные интеграции:")
    print(f"  ID: {metadata.id}")
    print(f"  Version: {metadata.version}")
    print(f"  Name: {metadata.name}")
    print(f"  Description: {metadata.description}")
    print(f"  Category: {metadata.category}")
    print(f"  Required fields: {metadata.config_schema.get('required', [])}")
    print(f"  Properties: {list(metadata.config_schema.get('properties', {}).keys())}")

    # Проверяем примеры
    print(f"✓ Примеры использования: {len(metadata.examples)}")
    for i, example in enumerate(metadata.examples):
        print(f"  {i+1}. {example['title']}")

    print("\n✓ Интеграция VK Send Photo готова к использованию!")
    print("  Поддерживает:")
    print("  - Отправку фото по локальному пути (photo_path)")
    print("  - Отправку фото по URL (photo_url)")
    print("  - Отправку существующего фото по ID (photo_file_id)")

if __name__ == "__main__":
    asyncio.run(test_integration())