"""Тесты для Telegram Edit Message интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.telegram.edit_message import TelegramEditMessageIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Telegram Edit Message интеграции."""
    return TelegramEditMessageIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "bot_token": "123456:ABC-DEF-test-token"
    })
    return resolver


@pytest.fixture
def credentials_resolver_with_payload():
    """Создает mock credentials resolver с payload."""
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


class TestTelegramEditMessageMetadata:
    """Тесты метаданных Telegram Edit Message интеграции."""
    
    def test_metadata_id(self, integration):
        """Тест ID метаданных."""
        assert integration.metadata.id == "telegram_edit_message"
    
    def test_metadata_version(self, integration):
        """Тест версии метаданных."""
        assert integration.metadata.version == "1.0.0"
    
    def test_metadata_name(self, integration):
        """Тест названия метаданных."""
        assert integration.metadata.name == "Telegram Edit Message"
    
    def test_metadata_category(self, integration):
        """Тест категории метаданных."""
        assert integration.metadata.category == "messaging"
    
    def test_metadata_credentials_provider(self, integration):
        """Тест провайдера credentials."""
        assert integration.metadata.credentials_provider == "telegram"
    
    def test_metadata_credentials_strategy(self, integration):
        """Тест стратегии credentials."""
        assert integration.metadata.credentials_strategy == "api_key"
    
    def test_metadata_icon(self, integration):
        """Тест иконки интеграции."""
        assert integration.metadata.icon_s3_key == "icons/integrations/telegram.svg"
    
    def test_metadata_color(self, integration):
        """Тест цвета интеграции."""
        assert integration.metadata.color == "#0088cc"
    
    def test_metadata_config_schema(self, integration):
        """Тест schema конфигурации."""
        schema = integration.metadata.config_schema
        assert schema["type"] == "object"
        assert set(schema["required"]) == {"chat_id", "message_id", "text"}
        assert "chat_id" in schema["properties"]
        assert "message_id" in schema["properties"]
        assert "text" in schema["properties"]
        assert "parse_mode" in schema["properties"]
    
    def test_metadata_examples(self, integration):
        """Тест примеров использования."""
        examples = integration.metadata.examples
        assert len(examples) > 0
        assert examples[0]["title"] == "Редактирование сообщения"
        assert "chat_id" in examples[0]["config"]
        assert "message_id" in examples[0]["config"]
        assert "text" in examples[0]["config"]


class TestTelegramEditMessageExecute:
    """Тесты выполнения Telegram Edit Message интеграции."""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, integration, credentials_resolver, logger, bot_id):
        """Тест успешного выполнения интеграции."""
        with patch('app.integrations.telegram.edit_message.Bot') as mock_bot_class:
            # Настраиваем mock сообщения
            mock_bot = MagicMock()
            mock_message = MagicMock()
            mock_message.message_id = 123
            mock_message.chat.id = 456
            mock_message.chat.type = "private"
            mock_message.text = "Updated test message"
            mock_message.date = 1234567890
            
            mock_bot.edit_message_text = AsyncMock(return_value=mock_message)
            mock_bot_class.return_value = mock_bot
            
            # Выполняем интеграцию
            result = await integration.execute(
                config={
                    "chat_id": "456",
                    "message_id": 123,
                    "text": "Updated test message"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем результат
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["message_id"] == 123
            assert result["response"]["result"]["chat"]["id"] == 456
            assert result["response"]["result"]["text"] == "Updated test message"
            
            # Проверяем, что методы были вызваны правильно
            mock_bot.edit_message_text.assert_called_once_with(
                chat_id="456",
                message_id=123,
                text="Updated test message",
                parse_mode=None
            )
            mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")
    
    @pytest.mark.asyncio
    async def test_execute_with_parse_mode(self, integration, credentials_resolver, logger, bot_id):
        """Тест выполнения с указанным parse_mode."""
        with patch('app.integrations.telegram.edit_message.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_message = MagicMock()
            mock_message.message_id = 123
            mock_message.chat.id = 456
            mock_message.chat.type = "private"
            mock_message.text = "<b>Updated message</b>"
            mock_message.date = 1234567890
            
            mock_bot.edit_message_text = AsyncMock(return_value=mock_message)
            mock_bot_class.return_value = mock_bot
            
            # Выполняем интеграцию с HTML parse_mode
            result = await integration.execute(
                config={
                    "chat_id": "456",
                    "message_id": 123,
                    "text": "<b>Updated message</b>",
                    "parse_mode": "HTML"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем результат
            assert result["response"]["ok"] is True
            
            # Проверяем, что parse_mode был передан
            mock_bot.edit_message_text.assert_called_once_with(
                chat_id="456",
                message_id=123,
                text="<b>Updated message</b>",
                parse_mode="HTML"
            )
    
    @pytest.mark.asyncio
    async def test_execute_with_payload_credentials(
        self, integration, credentials_resolver_with_payload, logger, bot_id
    ):
        """Тест выполнения с credentials в payload."""
        with patch('app.integrations.telegram.edit_message.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_message = MagicMock()
            mock_message.message_id = 123
            mock_message.chat.id = 456
            mock_message.chat.type = "private"
            mock_message.text = "Updated message"
            mock_message.date = 1234567890
            
            mock_bot.edit_message_text = AsyncMock(return_value=mock_message)
            mock_bot_class.return_value = mock_bot
            
            # Выполняем интеграцию
            result = await integration.execute(
                config={
                    "chat_id": "456",
                    "message_id": 123,
                    "text": "Updated message"
                },
                credentials_resolver=credentials_resolver_with_payload,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем результат
            assert result["response"]["ok"] is True
            
            # Проверяем, что токен был извлечен из payload
            mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")
    
    @pytest.mark.asyncio
    async def test_execute_no_credentials(self, integration, logger, bot_id):
        """Тест выполнения без credentials."""
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value=None)
        
        result = await integration.execute(
            config={
                "chat_id": "456",
                "message_id": 123,
                "text": "Updated message"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем ошибку
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "credentials" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_missing_bot_token(self, integration, logger, bot_id):
        """Тест выполнения без bot_token в credentials."""
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value={
            "payload": {"some_other_field": "value"}
        })
        
        result = await integration.execute(
            config={
                "chat_id": "456",
                "message_id": 123,
                "text": "Updated message"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем ошибку
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "bot_token" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_chat_id(self, integration, credentials_resolver, logger, bot_id):
        """Тест выполнения без chat_id."""
        result = await integration.execute(
            config={
                "message_id": 123,
                "text": "Updated message"
                # Отсутствует chat_id
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем ошибку
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "chat_id" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_message_id(self, integration, credentials_resolver, logger, bot_id):
        """Тест выполнения без message_id."""
        result = await integration.execute(
            config={
                "chat_id": "456",
                "text": "Updated message"
                # Отсутствует message_id
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем ошибку
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "message_id" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_text(self, integration, credentials_resolver, logger, bot_id):
        """Тест выполнения без text."""
        result = await integration.execute(
            config={
                "chat_id": "456",
                "message_id": 123
                # Отсутствует text
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем ошибку
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "text" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_telegram_error(self, integration, credentials_resolver, logger, bot_id):
        """Тест обработки TelegramError."""
        with patch('app.integrations.telegram.edit_message.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            telegram_error = Exception("Message not found")
            telegram_error.error_code = 400
            
            mock_bot.edit_message_text = AsyncMock(side_effect=telegram_error)
            mock_bot_class.return_value = mock_bot
            
            result = await integration.execute(
                config={
                    "chat_id": "456",
                    "message_id": 123,
                    "text": "Updated message"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем ошибку
            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 400
            assert "Message not found" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_unexpected_error(self, integration, credentials_resolver, logger, bot_id):
        """Тест обработки неожиданной ошибки."""
        with patch('app.integrations.telegram.edit_message.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.edit_message_text = AsyncMock(
                side_effect=ValueError("Unexpected error")
            )
            mock_bot_class.return_value = mock_bot
            
            result = await integration.execute(
                config={
                    "chat_id": "456",
                    "message_id": 123,
                    "text": "Updated message"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем ошибку
            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500
            assert "Unexpected error" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_type_conversion(self, integration, credentials_resolver, logger, bot_id):
        """Тест преобразования типов параметров."""
        with patch('app.integrations.telegram.edit_message.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_message = MagicMock()
            mock_message.message_id = 123
            mock_message.chat.id = 456
            mock_message.chat.type = "private"
            mock_message.text = "Updated message"
            mock_message.date = 1234567890
            
            mock_bot.edit_message_text = AsyncMock(return_value=mock_message)
            mock_bot_class.return_value = mock_bot
            
            # Передаем строки вместо int
            result = await integration.execute(
                config={
                    "chat_id": 456,  # int вместо str
                    "message_id": "123",  # str вместо int
                    "text": 999  # int вместо str
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем результат
            assert result["response"]["ok"] is True
            
            # Проверяем, что типы были правильно преобразованы
            mock_bot.edit_message_text.assert_called_once_with(
                chat_id="456",
                message_id=123,
                text="999",
                parse_mode=None
            )
    
    @pytest.mark.asyncio
    async def test_execute_library_not_available(self, logger, bot_id):
        """Тест выполнения когда библиотека недоступна."""
        integration = TelegramEditMessageIntegration()
        
        # Симулируем недоступность библиотеки
        with patch('app.integrations.telegram.edit_message.TELEGRAM_BOT_AVAILABLE', False):
            credentials_resolver = MagicMock(spec=CredentialsResolver)
            
            result = await integration.execute(
                config={
                    "chat_id": "456",
                    "message_id": 123,
                    "text": "Updated message"
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем ошибку
            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500
            assert "not installed" in result["response"]["description"]
