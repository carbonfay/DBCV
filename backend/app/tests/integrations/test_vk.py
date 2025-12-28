import asyncio
from uuid import UUID
from app.integrations.vk.send_photo import VkSendPhotoIntegration
import vk_api

class MockCredentialsResolver:
    async def get_default_for(self, bot_id, provider, strategy):
        return {"payload": {"access_token": "vk1.a.N3_f1e0x39pkAqiZfvjk5HKNXEhEC4SKxxpMXmXXlPEl06EXefmmI8gIlfQDGbtTzSnmUsdZGeiax7NJBb_UVAPIndhODylUOwxa6DPtQhCXniB4CHbSFULhHk3GiSzvmDNv_6LGUrhYpIYU9UF429Lx3P_bLw68hlXZlTAx5jvwCrM-gBose_YUY7xtGe-V18pGm8FIOGAtfhNeyDxnzA"}}

class MockLogger:
    async def error(self, msg):
        print(f"ERROR: {msg}")

async def test_vk():
    token = "vk1.a.N3_f1e0x39pkAqiZfvjk5HKNXEhEC4SKxxpMXmXXlPEl06EXefmmI8gIlfQDGbtTzSnmUsdZGeiax7NJBb_UVAPIndhODylUOwxa6DPtQhCXniB4CHbSFULhHk3GiSzvmDNv_6LGUrhYpIYU9UF429Lx3P_bLw68hlXZlTAx5jvwCrM-gBose_YUY7xtGe-V18pGm8FIOGAtfhNeyDxnzA"
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        user = vk.users.get()
        print("Token valid, user:", user)
    except Exception as e:
        print("Token invalid:", e)
        return

    integration = VkSendPhotoIntegration()
    resolver = MockCredentialsResolver()
    logger = MockLogger()
    bot_id = UUID("12345678-1234-1234-1234-123456789012")

    # Test with photo_path - but since photo.jpg is empty, it may fail
    config = {
        "peer_id": 9086628,  # User's own ID for testing
        "photo_path": "../../../tmp/photo.jpg",
        "message": "Test photo"
    }

    result = await integration.execute(config, resolver, bot_id, logger)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(test_vk())