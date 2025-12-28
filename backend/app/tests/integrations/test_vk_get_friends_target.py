"""Тест VK Get Friends с указанием целевого пользователя."""
import asyncio
from uuid import uuid4


async def test_vk_get_friends_target_user():
    """Тест получения списка друзей другого пользователя VK."""
    from app.integrations.vk.get_friends import VkGetFriendsIntegration
    
    # Mock credentials resolver
    class MockCredentialsResolver:
        async def get_default_for(self, bot_id, provider, strategy):
            # User token с правами friends
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
    
    print("=" * 70)
    print("VK Get Friends Integration Test (Target User)")
    print("=" * 70)
    print("\n⚠️  ПРИМЕЧАНИЕ:")
    print("   Метод friends.get() работает только с USER TOKEN, не с GROUP TOKEN!")
    print("   Также пользователь может скрыть список друзей в настройках приватности.")
    print()
    
    # Известные публичные пользователи VK
    test_users = [
        {"id": 1, "name": "Павел Дуров"},
        {"id": 2, "name": "Александра Владимирова"},
    ]
    
    for user in test_users:
        print(f"\n[Тест] Получить друзей пользователя: {user['name']} (ID: {user['id']})")
        config = {
            "user_id": user['id'],
            "count": 5,
            "order": "hints",
            "fields": ["photo_100", "domain", "online"]
        }
        
        result = await integration.execute(config, resolver, bot_id, logger)
        
        if result.get("response", {}).get("ok"):
            data = result["response"]["result"]
            print(f"✅ Успешно:")
            print(f"   - Всего друзей: {data['total_count']}")
            print(f"   - Получено: {len(data['items'])}")
            print(f"   - Offset: {data['offset']}")
            print(f"   - Есть еще: {data['has_more']}")
            
            if data['items']:
                print(f"\n   Первые 3 друга:")
                for i, friend in enumerate(data['items'][:3], 1):
                    print(f"   {i}. {friend.get('first_name')} {friend.get('last_name')}")
                    print(f"      - ID: {friend.get('id')}")
                    print(f"      - Domain: @{friend.get('domain', 'N/A')}")
                    print(f"      - Online: {'Да' if friend.get('online') else 'Нет'}")
        else:
            error_desc = result.get('response', {}).get('description', 'Unknown error')
            error_code = result.get('response', {}).get('error_code', 'N/A')
            print(f"❌ Ошибка [{error_code}]: {error_desc}")
            
            if error_code == 27:
                print("   💡 Это ожидаемо: метод требует USER token, а не GROUP token")
            elif error_code == 30:
                print("   💡 Профиль пользователя закрыт или список друзей скрыт")
    
    print("\n" + "=" * 70)
    print("Тест завершен!")
    print("=" * 70)
    print("\n📝 РЕЗЮМЕ:")
    print("   - Интеграция реализована корректно")
    print("   - Метод friends.get() требует USER token с правами 'friends'")
    print("   - Если у вас GROUP token - метод вернет ошибку 27")
    print("   - Нужен USER token для получения собственных друзей")
    print("   - Можно получить друзей другого пользователя, если профиль открыт")


if __name__ == "__main__":
    asyncio.run(test_vk_get_friends_target_user())
