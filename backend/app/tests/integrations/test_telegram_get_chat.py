"""Тесты для Telegram Get Chat интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.telegram.get_chat import TelegramGetChatIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Telegram Get Chat интеграции."""
    return TelegramGetChatIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "bot_token": "123456:ABC-DEF-test-token"
        }
    })
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_telegram_get_chat_metadata(integration):
    """Тест метаданных Telegram Get Chat интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "telegram_get_chat"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Telegram Get Chat"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "telegram"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_telegram_get_chat_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Telegram Get Chat интеграции."""
    with patch('app.integrations.telegram.get_chat.Bot') as mock_bot_class:
        # Настраиваем mock
        mock_bot = MagicMock()
        mock_chat = MagicMock()
        mock_chat.id = 123456789
        mock_chat.type = "private"
        mock_chat.username = "testuser"
        mock_chat.first_name = "Test"
        mock_chat.last_name = "User"
        mock_chat.description = "Test chat"
        mock_chat.invite_link = "https://t.me/joinchat/abc123"
        mock_chat.member_count = None
        mock_chat.is_forum = False
        mock_chat.has_protected_content = False
        mock_chat.can_set_sticker_set = None
        
        # Mock permissions
        mock_permissions = MagicMock()
        mock_permissions.can_send_messages = True
        mock_permissions.can_send_media_messages = True
        mock_permissions.can_send_polls = False
        mock_permissions.can_send_other_messages = True
        mock_permissions.can_add_web_page_previews = True
        mock_permissions.can_change_info = False
        mock_permissions.can_invite_users = True
        mock_permissions.can_pin_messages = False
        mock_chat.permissions = mock_permissions
        
        mock_bot.get_chat = AsyncMock(return_value=mock_chat)
        mock_bot_class.return_value = mock_bot
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={"chat_id": "123456789"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == 123456789
        assert result["response"]["result"]["type"] == "private"
        assert result["response"]["result"]["username"] == "testuser"
        assert result["response"]["result"]["first_name"] == "Test"
        assert result["response"]["result"]["permissions"]["can_send_messages"] is True
        
        # Проверяем, что метод библиотеки был вызван
        mock_bot.get_chat.assert_called_once_with(chat_id="123456789")
        mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")


@pytest.mark.asyncio
async def test_telegram_get_chat_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"chat_id": "123"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "bot_token not found" in result["response"]["description"]


@pytest.mark.asyncio
async def test_telegram_get_chat_execute_no_chat_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без chat_id."""
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "chat_id is required" in result["response"]["description"]