"""Тесты для интеграции Telegram Get Chat."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID

from app.integrations.telegram.get_chat import TelegramGetChatIntegration
from app.auth.credentials_resolver import CredentialsResolver


@pytest.fixture
def integration():
    """Фикстура для интеграции Telegram Get Chat."""
    return TelegramGetChatIntegration()


@pytest.fixture
def mock_credentials_resolver():
    """Фикстура для мокирования CredentialsResolver."""
    resolver = AsyncMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"bot_token": "test_token"}})
    return resolver


@pytest.fixture
def mock_logger():
    """Фикстура для мокирования BotLogger."""
    logger = AsyncMock()
    logger.error = AsyncMock()
    logger.info = AsyncMock()
    return logger


@pytest.mark.asyncio
async def test_telegram_get_chat_metadata(integration):
    """Тест метаданных интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "telegram_get_chat"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Telegram Get Chat"
    assert metadata.category == "messaging"
    assert "chat_id" in metadata.config_schema["properties"]


@pytest.mark.asyncio
async def test_telegram_get_chat_missing_chat_id(integration, mock_credentials_resolver, mock_logger):
    """Тест интеграции с отсутствующим chat_id."""
    config = {}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "chat_id is required" in result["response"]["description"]


@pytest.mark.asyncio
@patch('app.integrations.telegram.get_chat.Bot')
async def test_telegram_get_chat_success(mock_bot_class, integration, mock_credentials_resolver, mock_logger):
    """Тест успешного выполнения интеграции."""
    # Подготовим mock объекты
    mock_bot_instance = AsyncMock()
    mock_chat = MagicMock()
    
    # Настроим атрибуты mock чата
    mock_chat.id = 123456789
    mock_chat.type = "private"
    mock_chat.first_name = "Test"
    mock_chat.last_name = "User"
    mock_chat.username = "testuser"
    mock_chat.description = None
    mock_chat.permissions = None
    mock_chat.location = None
    mock_chat.photo = None
    
    mock_bot_instance.get_chat = AsyncMock(return_value=mock_chat)
    mock_bot_class.return_value = mock_bot_instance
    
    config = {"chat_id": "123456789"}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is True
    assert result["response"]["result"]["id"] == 123456789
    assert result["response"]["result"]["type"] == "private"
    assert result["response"]["result"]["first_name"] == "Test"
    assert result["response"]["result"]["last_name"] == "User"


@pytest.mark.asyncio
async def test_telegram_get_chat_missing_credentials(integration, mock_logger):
    """Тест интеграции с отсутствующими credentials."""
    config = {"chat_id": "123456789"}
    bot_id = UUID(int=1)
    
    # Создаем мок, который возвращает None
    mock_credentials_resolver = AsyncMock(spec=CredentialsResolver)
    mock_credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"]


@pytest.mark.asyncio
@patch('app.integrations.telegram.get_chat.Bot')
async def test_telegram_get_chat_telegram_error(mock_bot_class, integration, mock_credentials_resolver, mock_logger):
    """Тест обработки ошибки Telegram API."""
    from app.integrations.telegram.get_chat import TelegramError
    
    # Симулируем ошибку Telegram
    mock_bot_instance = AsyncMock()
    mock_bot_instance.get_chat.side_effect = TelegramError("Unauthorized")
    mock_bot_class.return_value = mock_bot_instance
    
    config = {"chat_id": "123456789"}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["description"] == "Unauthorized"


@pytest.mark.asyncio
async def test_telegram_get_chat_no_library(integration, mock_credentials_resolver, mock_logger):
    """Тест интеграции при отсутствии библиотеки."""
    # Изменяем значение переменной, чтобы симулировать отсутствие библиотеки
    original_telegram_available = integration.__class__.__module__.__dict__.get('TELEGRAM_BOT_AVAILABLE', True)
    
    # Создаем временное изменение для тестирования
    import app.integrations.telegram.get_chat as get_chat_module
    original_value = getattr(get_chat_module, 'TELEGRAM_BOT_AVAILABLE', True)
    get_chat_module.TELEGRAM_BOT_AVAILABLE = False
    
    try:
        config = {"chat_id": "123456789"}
        bot_id = UUID(int=1)
        
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"]
    finally:
        # Восстанавливаем оригинальное значение
        get_chat_module.TELEGRAM_BOT_AVAILABLE = original_value