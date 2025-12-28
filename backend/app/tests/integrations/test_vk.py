import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

# Импорты ваших классов
from app.integrations.vk_shinkevichOVKIPo_301.send_message import VkSendMessageIntegration
from app.integrations.vk_shinkevichOVKIPo_301.send_photo import VkSendPhotoIntegration
from app.integrations.vk_shinkevichOVKIPo_301.get_user import VkGetUserInfoIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# ==================== BYPASS DB (ОБМАНКА ДЛЯ БАЗЫ) ====================
# Эти фикстуры перекрывают те, что в conftest.py, 
# чтобы не требовать initdb и базу данных.

@pytest.fixture(scope="session")
async def engine():
    """Фейковый движок БД, чтобы не запускать initdb."""
    yield MagicMock()

@pytest.fixture(scope="function")
async def session():
    """Фейковая сессия БД."""
    yield MagicMock()

# ==================== FIXTURES (Настройки теста) ====================

@pytest.fixture
def mock_credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "token": "vk1.a.fake", "api_key": "vk1.a.fake"
    })
    return resolver

@pytest.fixture
def mock_logger():
    return MagicMock(spec=BotLogger)

@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")

# ==================== TESTS (Сами тесты) ====================

@pytest.mark.asyncio
async def test_vk_send_message_success(mock_credentials_resolver, mock_logger, bot_id):
    integration = VkSendMessageIntegration()
    with patch("app.integrations.vk.send_message.vk_api.VkApi") as MockVkApi:
        mock_vk = MockVkApi.return_value.get_api.return_value
        mock_vk.messages.send.return_value = 1001
        
        result = await integration.execute(
            config={"user_id": 123, "message": "Test"},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        assert result["response"]["ok"] is True
        assert result["response"]["result"] == 1001

@pytest.mark.asyncio
async def test_vk_send_photo_success(mock_credentials_resolver, mock_logger, bot_id):
    integration = VkSendPhotoIntegration()
    with patch("app.integrations.vk.send_photo.vk_api.VkApi") as MockVkApi,          patch("app.integrations.vk.send_photo.VkUpload") as MockVkUpload:
        
        mock_vk = MockVkApi.return_value.get_api.return_value
        mock_uploader = MockVkUpload.return_value
        mock_uploader.photo_messages.return_value = [{'owner_id': 1, 'id': 2}]
        
        result = await integration.execute(
            config={"user_id": 123, "photo_path": "cat.jpg", "caption": "C"},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        assert result["response"]["ok"] is True

@pytest.mark.asyncio
async def test_vk_get_user_success(mock_credentials_resolver, mock_logger, bot_id):
    integration = VkGetUserInfoIntegration()
    with patch("app.integrations.vk.get_user.vk_api.VkApi") as MockVkApi:
        mock_vk = MockVkApi.return_value.get_api.return_value
        mock_vk.users.get.return_value = [{"id": 1, "first_name": "Pavel", "last_name": "Durov", "city": {"title": "Dubai"}}]
        
        result = await integration.execute(
            config={"user_id": "1"},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["first_name"] == "Pavel"
