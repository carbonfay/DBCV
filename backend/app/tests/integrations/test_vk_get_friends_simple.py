"""Простой тест для VK Get Friends интеграции."""
import asyncio
from uuid import uuid4


async def test_vk_get_friends():
    """Тест получения списка друзей пользователя VK."""
    from app.integrations.vk.get_friends import VkGetFriendsIntegration
    
    # Mock credentials resolver
    class MockCredentialsResolver:
        async def get_default_for(self, bot_id, provider, strategy):
            # ЗАМЕНИ ЭТОТ ТОКЕН НА СВОЙ!
            return {
                "payload": {
                    "access_token": "vk1.a.flXjZR6hUiN1ASHRNp1YlhcxDEdcKigX08ze5I5IuM_hnHfnAtjy8APFFOyBsAG5iu-n9Tn3DLZe7jyn8m_qP1M7PKKfVDDhVdR5CyF8oHZmTviczkVus_4s0SqJT0AhvnyzzhRyluO3SoVNUrxJ4yO38Gh2SDcSrjmZuwbQz2WaEZVanZrs1fvjZUc8eBWB-xvXx2ARCAx8_C0rVyScZA"
                }
            }
    
    # Mock logger
    class MockLogger:
        async def info(self, msg):
            print(f"[INFO] {msg}")
        
        async def error(self, msg):
            print(f"[ERROR] {msg}")
    
    integration = VkGetFriendsIntegration()
    resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = uuid4()
    
    print("=" * 60)
    print("VK Get Friends Integration Test")
    print("=" * 60)
    
    # Тест 1: Получить своих друзей (первые 5)
    print("\n[Тест 1] Получить своих друзей (первые 5)")
    config1 = {
        "count": 5,
        "fields": ["photo_100", "online", "domain"]
    }
    
    result1 = await integration.execute(config1, resolver, bot_id, logger)
    print(f"Результат: {result1}")
    
    if result1.get("response", {}).get("ok"):
        data = result1["response"]["result"]
        print(f"✅ Друзей получено:")
        print(f"   - Всего друзей: {data['total_count']}")
        print(f"   - Получено в запросе: {len(data['items'])}")
        print(f"   - Есть еще: {data['has_more']}")
        
        if data['items']:
            print(f"\n   Первые друзья:")
            for i, friend in enumerate(data['items'][:3], 1):
                print(f"   {i}. {friend.get('first_name')} {friend.get('last_name')}")
                print(f"      - ID: {friend.get('id')}")
                print(f"      - Domain: {friend.get('domain', 'N/A')}")
                print(f"      - Online: {friend.get('online', 'N/A')}")
    else:
        print(f"❌ Ошибка: {result1.get('response', {}).get('description')}")
    
    # Тест 2: Получить друзей с расширенными полями
    print("\n[Тест 2] Получить друзей с расширенными полями (3 друга)")
    config2 = {
        "count": 3,
        "order": "name",
        "fields": ["photo_100", "online", "city", "bdate", "status"]
    }
    
    result2 = await integration.execute(config2, resolver, bot_id, logger)
    print(f"Результат: {result2}")
    
    if result2.get("response", {}).get("ok"):
        data = result2["response"]["result"]
        print(f"✅ Расширенная информация о друзьях:")
        
        if data['items']:
            for i, friend in enumerate(data['items'], 1):
                print(f"\n   {i}. {friend.get('first_name')} {friend.get('last_name')}")
                print(f"      - ID: {friend.get('id')}")
                print(f"      - Domain: @{friend.get('domain', 'N/A')}")
                
                if 'city' in friend:
                    print(f"      - Город: {friend['city'].get('title', 'N/A')}")
                else:
                    print(f"      - Город: N/A")
                
                print(f"      - Дата рождения: {friend.get('bdate', 'N/A')}")
                print(f"      - Статус: {friend.get('status', 'N/A')}")
                print(f"      - Онлайн: {'Да' if friend.get('online') else 'Нет'}")
    else:
        print(f"❌ Ошибка: {result2.get('response', {}).get('description')}")
    
    # Тест 3: Пагинация - получить вторую страницу
    print("\n[Тест 3] Пагинация - вторая страница (offset=5, count=3)")
    config3 = {
        "count": 3,
        "offset": 5,
        "order": "hints",
        "fields": ["photo_100", "domain"]
    }
    
    result3 = await integration.execute(config3, resolver, bot_id, logger)
    print(f"Результат: {result3}")
    
    if result3.get("response", {}).get("ok"):
        data = result3["response"]["result"]
        print(f"✅ Пагинация:")
        print(f"   - Всего друзей: {data['total_count']}")
        print(f"   - Текущий offset: {data['offset']}")
        print(f"   - Получено: {len(data['items'])} друзей")
        print(f"   - Есть еще: {data['has_more']}")
        
        if data['items']:
            print(f"\n   Друзья на странице 2:")
            for i, friend in enumerate(data['items'], 1):
                print(f"   {i}. {friend.get('first_name')} {friend.get('last_name')} (@{friend.get('domain', 'N/A')})")
    else:
        print(f"❌ Ошибка: {result3.get('response', {}).get('description')}")
    
    print("\n" + "=" * 60)
    print("Тест завершен!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_vk_get_friends())
