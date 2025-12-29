"""Тесты для Telegram Get User интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.telegram.get_user import TelegramGetUserIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Telegram Get User интеграции."""
    return TelegramGetUserIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "bot_token": "123456:ABC-DEF-test-token"
        }
    })
    resolver.get_single_for = AsyncMock(return_value={
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


def test_telegram_get_user_metadata(integration):
    """Тест метаданных Telegram Get User интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "telegram_get_user"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Telegram Get User"
    assert metadata.description == "Получение информации о боте через Bot API (getMe)"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "telegram"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "python-telegram-bot>=20.0" or metadata.library_name is None


@pytest.mark.asyncio
async def test_telegram_get_user_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Telegram Get User интеграции."""
    with patch('app.integrations.telegram.get_user.Bot') as mock_bot_class:
        # Настраиваем mock
        mock_bot = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.is_bot = True
        mock_user.first_name = "TestBot"
        mock_user.username = "test_bot"
        mock_user.last_name = None
        mock_user.language_code = "en"
        mock_user.can_join_groups = True
        mock_user.can_read_all_group_messages = False
        mock_user.supports_inline_queries = False
        mock_user.to_dict = MagicMock(return_value={
            "id": 123456789,
            "is_bot": True,
            "first_name": "TestBot",
            "username": "test_bot",
            "can_join_groups": True,
            "can_read_all_group_messages": False,
            "supports_inline_queries": False
        })
        
        mock_bot.get_me = AsyncMock(return_value=mock_user)
        mock_bot_class.return_value = mock_bot
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={},  # getMe не требует параметров
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == 123456789
        assert result["response"]["result"]["is_bot"] is True
        assert result["response"]["result"]["first_name"] == "TestBot"
        assert result["response"]["result"]["username"] == "test_bot"
        
        # Проверяем, что метод библиотеки был вызван
        mock_bot.get_me.assert_called_once()
        mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")


@pytest.mark.asyncio
async def test_telegram_get_user_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения Get User без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    credentials_resolver.get_single_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_telegram_get_user_execute_missing_bot_token(integration, logger, bot_id):
    """Тест выполнения Get User с credentials без bot_token."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}  # Пустой payload без bot_token
    })
    credentials_resolver.get_single_for = AsyncMock(return_value={
        "payload": {}
    })
    
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "bot_token" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_telegram_get_user_execute_telegram_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки Telegram API."""
    with patch('app.integrations.telegram.get_user.Bot') as mock_bot_class:
        from telegram.error import TelegramError
        
        mock_bot = MagicMock()
        mock_error = TelegramError("Invalid token")
        mock_error.error_code = 401
        mock_bot.get_me = AsyncMock(side_effect=mock_error)
        mock_bot_class.return_value = mock_bot
        
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "Invalid token" in result["response"]["description"]


@pytest.mark.asyncio
async def test_telegram_get_user_execute_with_token_in_root(integration, logger, bot_id):
    """Тест выполнения Get User с token в корне credentials (обратная совместимость)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "token": "123456:ABC-DEF-test-token"  # token в корне, не в payload
    })
    credentials_resolver.get_single_for = AsyncMock(return_value=None)
    
    with patch('app.integrations.telegram.get_user.Bot') as mock_bot_class:
        mock_bot = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.is_bot = True
        mock_user.first_name = "TestBot"
        mock_user.username = "test_bot"
        mock_user.to_dict = MagicMock(return_value={
            "id": 123456789,
            "is_bot": True,
            "first_name": "TestBot",
            "username": "test_bot"
        })
        
        mock_bot.get_me = AsyncMock(return_value=mock_user)
        mock_bot_class.return_value = mock_bot
        
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == 123456789


@pytest.mark.asyncio
async def test_telegram_get_user_execute_user_without_to_dict(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения Get User когда User объект не имеет метода to_dict."""
    with patch('app.integrations.telegram.get_user.Bot') as mock_bot_class:
        mock_bot = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.is_bot = True
        mock_user.first_name = "TestBot"
        mock_user.username = "test_bot"
        mock_user.last_name = None
        mock_user.language_code = "en"
        mock_user.can_join_groups = True
        mock_user.can_read_all_group_messages = False
        mock_user.supports_inline_queries = False
        # Убираем метод to_dict
        del mock_user.to_dict
        
        mock_bot.get_me = AsyncMock(return_value=mock_user)
        mock_bot_class.return_value = mock_bot
        
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == 123456789
        assert result["response"]["result"]["is_bot"] is True
        assert result["response"]["result"]["first_name"] == "TestBot"
        assert result["response"]["result"]["username"] == "test_bot"

