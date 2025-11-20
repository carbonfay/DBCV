"""Тесты для Telegram интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.telegram.send_message import TelegramSendMessageIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Telegram интеграции."""
    return TelegramSendMessageIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "bot_token": "123456:ABC-DEF-test-token"
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


def test_telegram_metadata(integration):
    """Тест метаданных Telegram интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "telegram_send_message"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Telegram Send Message"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "telegram"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_telegram_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Telegram интеграции."""
    with patch('app.integrations.telegram.send_message.Bot') as mock_bot_class:
        # Настраиваем mock
        mock_bot = MagicMock()
        mock_message = MagicMock()
        mock_message.message_id = 123
        mock_message.chat.id = 456
        mock_message.chat.type = "private"
        mock_message.text = "Test message"
        mock_message.date = 1234567890
        
        mock_bot.send_message = AsyncMock(return_value=mock_message)
        mock_bot_class.return_value = mock_bot
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "chat_id": "123",
                "text": "Test message"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["message_id"] == 123
        assert result["response"]["result"]["chat"]["id"] == 456
        
        # Проверяем, что метод библиотеки был вызван
        mock_bot.send_message.assert_called_once()
        mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")


@pytest.mark.asyncio
async def test_telegram_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"chat_id": "123", "text": "Test"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_telegram_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими параметрами."""
    result = await integration.execute(
        config={},  # Отсутствуют chat_id и text
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400

