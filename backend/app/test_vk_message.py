import asyncio
from app.integrations.vk.send_message import VkSendMessageIntegration

# ТВОИ ДАННЫЕ
MY_TOKEN = "vk1.a.7o7doqbyMDk8RPB1RZWrsB68VH-mDE7Ugeo_wu4yviaWN8oQ0foHRh7J7WvxXH-p8OklzSwEDo7ChQZwqm8SIuYEnRShC_Cvr8MWvKL1yqJqZX2MTdLHzyQHjr7gp5vj21r9Tb6G4-taC2MJd9XmLWyGkYzcpl8fVjq3N3UvEJevnV1dsBrlto5h4r2jGxqMwtECOEVGU0O0beOad0AOeA"
MY_USER_ID = 138201086

# Заглушки для системы (чтобы не лезть в базу данных)
class MockResolver:
    async def get_default_for(self, *args, **kwargs): return {"token": MY_TOKEN}
class MockLogger:
    def error(self, m): print(f"❌ ERR: {m}")
    def info(self, m): print(f"ℹ️ INF: {m}")

async def main():
    print(f"🚀 [Message] Отправляем сообщение...")
    
    integration = VkSendMessageIntegration()
    result = await integration.execute(
        config={
            "user_id": MY_USER_ID, 
            "message": "Привет! Это проверка связи из терминала. ✅"
        },
        credentials_resolver=MockResolver(),
        bot_id=None,
        logger=MockLogger()
    )
    print("🏁 РЕЗУЛЬТАТ:", result)

if __name__ == "__main__":
    asyncio.run(main())


# запуск docker-compose -f docker-compose.dev.yml exec backend python test_vk_message.py