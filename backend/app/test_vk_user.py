import asyncio
from app.integrations.vk.get_user import VkGetUserInfoIntegration

# ТВОИ ДАННЫЕ
MY_TOKEN = "vk1.a.7o7doqbyMDk8RPB1RZWrsB68VH-mDE7Ugeo_wu4yviaWN8oQ0foHRh7J7WvxXH-p8OklzSwEDo7ChQZwqm8SIuYEnRShC_Cvr8MWvKL1yqJqZX2MTdLHzyQHjr7gp5vj21r9Tb6G4-taC2MJd9XmLWyGkYzcpl8fVjq3N3UvEJevnV1dsBrlto5h4r2jGxqMwtECOEVGU0O0beOad0AOeA"

# ID Павла Дурова 1 для теста
TARGET_ID = "138201086" 

class MockResolver:
    async def get_default_for(self, *args, **kwargs): return {"token": MY_TOKEN}
class MockLogger:
    def error(self, m): print(f"❌ ERR: {m}")
    def info(self, m): print(f"ℹ️ INF: {m}")

async def main():
    print(f"🔎 [Get User] Получаем информацию о ID: {TARGET_ID}...")
    
    integration = VkGetUserInfoIntegration()
    result = await integration.execute(
        config={"user_id": TARGET_ID},
        credentials_resolver=MockResolver(),
        bot_id=None,
        logger=MockLogger()
    )
    
    if result.get("response", {}).get("ok"):
        print("\n✅ УСПЕХ! Красивый вывод:")
        print("-" * 30)
        # Выводим то самое красивое сообщение
        print(result["response"]["result"]["formatted_text"])
        print("-" * 30)
    else:
        print("❌ Ошибка:", result)

if __name__ == "__main__":
    asyncio.run(main())

# запуск docker-compose -f docker-compose.dev.yml exec backend python test_vk_user.py