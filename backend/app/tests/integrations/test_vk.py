import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

# ИМПОРТИРУЕМ ИЗ ТВОЕЙ УНИКАЛЬНОЙ ПАПКИ
from app.integrations.vk_shinkevich_ovkipo_301.send_message import VkSendMessageIntegration
from app.integrations.vk_shinkevich_ovkipo_301.send_photo import VkSendPhotoIntegration
from app.integrations.vk_shinkevich_ovkipo_301.get_user import VkGetUserInfoIntegration

from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# --- BYPASS DB ---
@pytest.fixture(scope="session")
async def engine(): yield MagicMock()
@pytest.fixture(scope="function")
async def session(): yield MagicMock()

# --- FIXTURES ---
@pytest.fixture
def mock_creds():
    r = MagicMock(spec=CredentialsResolver)
    r.get_default_for = AsyncMock(return_value={"token": "test"})
    return r

@pytest.fixture
def mock_log(): return MagicMock(spec=BotLogger)
@pytest.fixture
def bot_id(): return UUID("12345678-1234-5678-1234-567812345678")

# --- TESTS ---
@pytest.mark.asyncio
async def test_vk_message(mock_creds, mock_log, bot_id):
    # ПАТЧИМ ТОЖЕ В ТВОЕЙ ПАПКЕ
    with patch("app.integrations.vk_shinkevich_ovkipo_301.send_message.vk_api.VkApi") as m:
        m.return_value.get_api.return_value.messages.send.return_value = 1
        res = await VkSendMessageIntegration().execute({"user_id": 1, "message": "t"}, mock_creds, bot_id, mock_log)
        assert res["response"]["ok"] is True

@pytest.mark.asyncio
async def test_vk_photo(mock_creds, mock_log, bot_id):
    with patch("app.integrations.vk_shinkevich_ovkipo_301.send_photo.vk_api.VkApi") as m,          patch("app.integrations.vk_shinkevich_ovkipo_301.send_photo.VkUpload") as u:
        m.return_value.get_api.return_value.messages.send.return_value = 1
        u.return_value.photo_messages.return_value = [{"owner_id":1,"id":1}]
        res = await VkSendPhotoIntegration().execute({"user_id": 1, "photo_path": "a", "caption": "c"}, mock_creds, bot_id, mock_log)
        assert res["response"]["ok"] is True

@pytest.mark.asyncio
async def test_vk_user(mock_creds, mock_log, bot_id):
    with patch("app.integrations.vk_shinkevich_ovkipo_301.get_user.vk_api.VkApi") as m:
        m.return_value.get_api.return_value.users.get.return_value = [{"id":1,"first_name":"A","last_name":"B"}]
        res = await VkGetUserInfoIntegration().execute({"user_id": "1"}, mock_creds, bot_id, mock_log)
        assert res["response"]["ok"] is True
