"""Простой тест для VK Get Group интеграции."""
import asyncio
from uuid import uuid4


async def test_vk_get_group():
    """Тест получения информации о группе VK."""
    from app.integrations.vk.get_group import VkGetGroupIntegration
    
    # Mock credentials resolver
    class MockCredentialsResolver:
        async def get_default_for(self, bot_id, provider, strategy):
            # ЗАМЕНИ ЭТОТ ТОКЕН НА СВОЙ!
            return {
                "payload": {
                    "access_token": "vk1.a.4WRHln_zYompJA0dQE3LJHePeu6v_G--mX7bv04EROD_Uf_tNKqTaWwudrT7IC-89gcIRO3wFrupRPD1NXDlQ5Ck9Tuc1ngkZlw2ZXp4fgJadg1LhXsxu_qssrtcPJpY8O-GBEw9tMGLQmSUTdDKIsVWXZPDMlaMVn_bWH4WsPmeTn7dQgid4bdn4-TqdXrTOQP8JK6b6Y-d6xchInSdIA"
                }
            }
    
    # Mock logger
    class MockLogger:
        async def info(self, msg):
            print(f"[INFO] {msg}")
        
        async def error(self, msg):
            print(f"[ERROR] {msg}")
    
    integration = VkGetGroupIntegration()
    resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = uuid4()
    
    print("=" * 60)
    print("VK Get Group Integration Test")
    print("=" * 60)
    
    # Тест 1: Получить информацию о группе API VK (apiclub)
    print("\n[Тест 1] Базовая информация о группе (apiclub)")
    config1 = {
        "group_id": "apiclub",
        "fields": ["description", "members_count", "activity"]
    }
    
    result1 = await integration.execute(config1, resolver, bot_id, logger)
    print(f"Результат: {result1}")
    
    if result1.get("response", {}).get("ok"):
        groups = result1["response"]["result"]["groups"]
        if groups:
            group = groups[0]
            print(f"✅ Группа найдена:")
            print(f"   - ID: {group.get('id')}")
            print(f"   - Название: {group.get('name')}")
            print(f"   - Тип: {group.get('type')}")
            print(f"   - Участников: {group.get('members_count', 'N/A')}")
            print(f"   - Активность: {group.get('activity', 'N/A')}")
    else:
        print(f"❌ Ошибка: {result1.get('response', {}).get('description')}")
    
    # Тест 2: Получить расширенную информацию о группе VK (ID: 1)
    print("\n[Тест 2] Расширенная информация о группе VK (ID: 1)")
    config2 = {
        "group_id": "1",
        "fields": [
            "description",
            "members_count",
            "activity",
            "city",
            "country",
            "site",
            "verified",
            "can_post",
            "can_message"
        ]
    }
    
    result2 = await integration.execute(config2, resolver, bot_id, logger)
    print(f"Результат: {result2}")
    
    if result2.get("response", {}).get("ok"):
        groups = result2["response"]["result"]["groups"]
        if groups:
            group = groups[0]
            print(f"✅ Расширенная информация:")
            print(f"   - Название: {group.get('name')}")
            print(f"   - Описание: {group.get('description', 'N/A')[:100]}...")
            print(f"   - Участников: {group.get('members_count', 'N/A')}")
            print(f"   - Сайт: {group.get('site', 'N/A')}")
            print(f"   - Верифицирована: {group.get('verified', 'N/A')}")
            print(f"   - Можно писать: {group.get('can_message', 'N/A')}")
    else:
        print(f"❌ Ошибка: {result2.get('response', {}).get('description')}")
    
    # Тест 3: Получить информацию о популярной группе
    print("\n[Тест 3] Информация о группе VK Team (vkteam)")
    config3 = {
        "group_id": "vkteam",
        "fields": ["description", "members_count", "verified", "site"]
    }
    
    result3 = await integration.execute(config3, resolver, bot_id, logger)
    print(f"Результат: {result3}")
    
    if result3.get("response", {}).get("ok"):
        groups = result3["response"]["result"]["groups"]
        if groups:
            group = groups[0]
            print(f"✅ Информация о группе:")
            print(f"   - Название: {group.get('name')}")
            print(f"   - ID: {group.get('id')}")
            print(f"   - Screen name: {group.get('screen_name')}")
            print(f"   - Участников: {group.get('members_count', 'N/A')}")
            print(f"   - Верифицирована: {group.get('verified', 'N/A')}")
    else:
        print(f"❌ Ошибка: {result3.get('response', {}).get('description')}")
    
    print("\n" + "=" * 60)
    print("Тест завершен!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_vk_get_group())
