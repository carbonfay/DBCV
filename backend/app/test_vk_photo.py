import asyncio
import os
from app.integrations.vk.send_photo import VkSendPhotoIntegration

# ТВОИ ДАННЫЕ
MY_TOKEN = "vk1.a.7o7doqbyMDk8RPB1RZWrsB68VH-mDE7Ugeo_wu4yviaWN8oQ0foHRh7J7WvxXH-p8OklzSwEDo7ChQZwqm8SIuYEnRShC_Cvr8MWvKL1yqJqZX2MTdLHzyQHjr7gp5vj21r9Tb6G4-taC2MJd9XmLWyGkYzcpl8fVjq3N3UvEJevnV1dsBrlto5h4r2jGxqMwtECOEVGU0O0beOad0AOeA"
MY_USER_ID = 138201086

class MockResolver:
    async def get_default_for(self, *args, **kwargs): return {"token": MY_TOKEN}
class MockLogger:
    def error(self, m): print(f"❌ ERR: {m}")
    def info(self, m): print(f"ℹ️ INF: {m}")

async def main():
    # Файл должен лежать рядом со скриптом в папке backend
    photo_path = "cat.jpg"
    
    if not os.path.exists(photo_path):
        print(f"❌ ОШИБКА: Файл '{photo_path}' не найден!")
        print("Пожалуйста, положи файл cat.jpg в папку backend.")
        return

    print(f"🚀 [Photo] Отправляем кота ({photo_path})...")
    
    integration = VkSendPhotoIntegration()
    result = await integration.execute(
        config={
            "user_id": MY_USER_ID, 
            "photo_path": photo_path, 
            "caption": "Смотри какой кот! 🐈"
        },
        credentials_resolver=MockResolver(),
        bot_id=None,
        logger=MockLogger()
    )
    print("🏁 РЕЗУЛЬТАТ:", result)

if __name__ == "__main__":
    asyncio.run(main())


# запуск docker-compose -f docker-compose.dev.yml exec backend python test_vk_photo.py