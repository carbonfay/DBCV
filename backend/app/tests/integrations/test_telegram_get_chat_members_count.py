"""Тесты для Telegram Get Chat Members Count интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.telegram.get_chat_members_count import TelegramGetChatMembersCountIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Telegram Get Chat Members Count интеграции."""
    return TelegramGetChatMembersCountIntegration()


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
def credentials_resolver_with_token():
    """Создает mock credentials resolver с токеном как 'token'."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "token": "123456:ABC-DEF-test-token"
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


class TestTelegramGetChatMembersCountMetadata:
    """Тесты метаданных Telegram Get Chat Members Count интеграции."""
    
    def test_metadata_id(self, integration):
        """Тест ID метаданных."""
        assert integration.metadata.id == "telegram_get_chat_members_count"
    
    def test_metadata_version(self, integration):
        """Тест версии метаданных."""
        assert integration.metadata.version == "1.0.0"
    
    def test_metadata_name(self, integration):
        """Тест названия метаданных."""
        assert integration.metadata.name == "Telegram Get Chat Members Count"
    
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
    
    def test_metadata_library_name(self, integration):
        """Тест названия библиотеки."""
        assert "python-telegram-bot" in integration.metadata.library_name
    
    def test_metadata_config_schema(self, integration):
        """Тест schema конфигурации."""
        schema = integration.metadata.config_schema
        assert schema["type"] == "object"
        assert schema["required"] == ["chat_id"]
        assert "chat_id" in schema["properties"]
        
        chat_id_schema = schema["properties"]["chat_id"]
        assert chat_id_schema["type"] == "string"
        assert chat_id_schema["title"] == "Chat ID"
    
    def test_metadata_examples(self, integration):
        """Тест примеров использования."""
        examples = integration.metadata.examples
        assert len(examples) >= 2
        assert examples[0]["title"] == "Получить количество членов чата"
        assert examples[1]["title"] == "Получить количество членов группы используя переменную"


class TestTelegramGetChatMembersCountExecute:
    """Тесты выполнения Telegram Get Chat Members Count интеграции."""
    
    @pytest.mark.asyncio
    async def test_execute_success_with_chat_id(self, integration, credentials_resolver, logger, bot_id):
        """Тест успешного получения количества членов чата."""
        with patch('app.integrations.telegram.get_chat_members_count.Bot') as mock_bot_class:
            # Настраиваем mock
            mock_bot = MagicMock()
            mock_bot.get_chat_member_count = AsyncMock(return_value=42)
            mock_bot_class.return_value = mock_bot
            
            # Выполняем интеграцию
            result = await integration.execute(
                config={"chat_id": "-1001234567890"},
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            # Проверяем результат
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["members_count"] == 42
            assert result["response"]["result"]["chat_id"] == "-1001234567890"
            
            # Проверяем, что метод библиотеки был вызван
            mock_bot.get_chat_member_count.assert_called_once_with(chat_id="-1001234567890")
            mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")
    
    @pytest.mark.asyncio
    async def test_execute_success_with_payload(self, integration, credentials_resolver_with_payload, logger, bot_id):
        """Тест успешного выполнения с credentials в payload."""
        with patch('app.integrations.telegram.get_chat_members_count.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_chat_member_count = AsyncMock(return_value=100)
            mock_bot_class.return_value = mock_bot
            
            result = await integration.execute(
                config={"chat_id": "123456"},
                credentials_resolver=credentials_resolver_with_payload,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["members_count"] == 100
            mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")
    
    @pytest.mark.asyncio
    async def test_execute_success_with_token_field(self, integration, credentials_resolver_with_token, logger, bot_id):
        """Тест успешного выполнения когда credentials используют поле 'token' вместо 'bot_token'."""
        with patch('app.integrations.telegram.get_chat_members_count.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_chat_member_count = AsyncMock(return_value=55)
            mock_bot_class.return_value = mock_bot
            
            result = await integration.execute(
                config={"chat_id": "789"},
                credentials_resolver=credentials_resolver_with_token,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["members_count"] == 55
            mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")
    
    @pytest.mark.asyncio
    async def test_execute_no_credentials(self, integration, logger, bot_id):
        """Тест выполнения без credentials."""
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value=None)
        
        result = await integration.execute(
            config={"chat_id": "123"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем ошибку
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "bot_token" in result["response"]["description"]
        
        # Проверяем, что логгер был вызван
        logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_no_bot_token_in_credentials(self, integration, logger, bot_id):
        """Тест выполнения когда нет bot_token в credentials."""
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value={
            "payload": {
                "some_field": "value"
            }
        })
        
        result = await integration.execute(
            config={"chat_id": "123"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "bot_token" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_chat_id(self, integration, credentials_resolver, logger, bot_id):
        """Тест выполнения когда отсутствует chat_id."""
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "chat_id" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_empty_chat_id(self, integration, credentials_resolver, logger, bot_id):
        """Тест выполнения с пустым chat_id."""
        result = await integration.execute(
            config={"chat_id": ""},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
    
    @pytest.mark.asyncio
    async def test_execute_telegram_error(self, integration, credentials_resolver, logger, bot_id):
        """Тест обработки Telegram ошибки."""
        with patch('app.integrations.telegram.get_chat_members_count.Bot') as mock_bot_class:
            # Создаем mock ошибку с error_code
            mock_error = MagicMock()
            mock_error.error_code = 400
            mock_error.__str__ = MagicMock(return_value="Bad Request: chat_id not found")
            
            mock_bot = MagicMock()
            from telegram.error import TelegramError
            # Используем реальный TelegramError, но мокируем его
            mock_bot.get_chat_member_count = AsyncMock(side_effect=mock_error)
            mock_bot_class.return_value = mock_bot
            
            with patch('app.integrations.telegram.get_chat_members_count.TelegramError', side_effect=lambda *args: mock_error):
                result = await integration.execute(
                    config={"chat_id": "invalid"},
                    credentials_resolver=credentials_resolver,
                    bot_id=bot_id,
                    logger=logger
                )
                
                assert result["response"]["ok"] is False
                assert result["response"]["error_code"] in [400, 500]
    
    @pytest.mark.asyncio
    async def test_execute_unexpected_error(self, integration, credentials_resolver, logger, bot_id):
        """Тест обработки неожиданной ошибки."""
        with patch('app.integrations.telegram.get_chat_members_count.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_chat_member_count = AsyncMock(side_effect=ValueError("Some unexpected error"))
            mock_bot_class.return_value = mock_bot
            
            result = await integration.execute(
                config={"chat_id": "123"},
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500
            assert "Some unexpected error" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_chat_id_conversion_to_string(self, integration, credentials_resolver, logger, bot_id):
        """Тест преобразования chat_id в строку."""
        with patch('app.integrations.telegram.get_chat_members_count.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.get_chat_member_count = AsyncMock(return_value=25)
            mock_bot_class.return_value = mock_bot
            
            # Передаем числовой chat_id
            result = await integration.execute(
                config={"chat_id": 12345},
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is True
            # Проверяем, что chat_id был преобразован в строку
            mock_bot.get_chat_member_count.assert_called_once_with(chat_id="12345")


class TestTelegramGetChatMembersCountLibraryAvailability:
    """Тесты проверки доступности библиотеки."""
    
    @pytest.mark.asyncio
    async def test_execute_library_not_available(self, logger, bot_id):
        """Тест выполнения когда библиотека не доступна."""
        with patch('app.integrations.telegram.get_chat_members_count.TELEGRAM_BOT_AVAILABLE', False):
            integration = TelegramGetChatMembersCountIntegration()
            credentials_resolver = MagicMock(spec=CredentialsResolver)
            
            result = await integration.execute(
                config={"chat_id": "123"},
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500
            assert "not installed" in result["response"]["description"]
