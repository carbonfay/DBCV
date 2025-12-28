"""Тесты для VK интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.vk.send_message import VkSendMessageIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр VK интеграции."""
    return VkSendMessageIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "access_token": "test_vk_access_token_123456"
        }
    })
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    mock_logger = MagicMock(spec=BotLogger)
    mock_logger.error = AsyncMock()
    return mock_logger


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_vk_metadata(integration):
    """Тест метаданных VK интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "vk_send_message"
    assert metadata.version == "1.0.0"
    assert metadata.name == "VK Send Message"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "vk"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.color == "#0077FF"


@pytest.mark.asyncio
async def test_vk_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения VK интеграции."""
    with patch('app.integrations.vk.send_message.vk_api') as mock_vk_api:
        # Настраиваем mock VK API
        mock_vk_session = MagicMock()
        mock_vk = MagicMock()
        mock_vk.messages.send = MagicMock(return_value=12345)  # message_id
        mock_vk_session.get_api.return_value = mock_vk
        mock_vk_api.VkApi.return_value = mock_vk_session
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "user_id": "123456",
                "message": "Тестовое сообщение"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["message_id"] == 12345
        assert result["response"]["result"]["user_id"] == 123456
        assert result["response"]["result"]["message"] == "Тестовое сообщение"
        assert "random_id" in result["response"]["result"]
        
        # Проверяем, что метод библиотеки был вызван
        mock_vk_api.VkApi.assert_called_once_with(token="test_vk_access_token_123456")
        mock_vk.messages.send.assert_called_once()


@pytest.mark.asyncio
async def test_vk_execute_with_keyboard(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения VK интеграции с клавиатурой."""
    with patch('app.integrations.vk.send_message.vk_api') as mock_vk_api:
        mock_vk_session = MagicMock()
        mock_vk = MagicMock()
        mock_vk.messages.send = MagicMock(return_value=67890)
        mock_vk_session.get_api.return_value = mock_vk
        mock_vk_api.VkApi.return_value = mock_vk_session
        
        keyboard = {
            "one_time": False,
            "buttons": [[{
                "action": {"type": "text", "label": "Кнопка 1"},
                "color": "primary"
            }]]
        }
        
        result = await integration.execute(
            config={
                "user_id": "789012",
                "message": "Выберите опцию",
                "keyboard": keyboard,
                "random_id": 999
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["message_id"] == 67890
        assert result["response"]["result"]["random_id"] == 999


@pytest.mark.asyncio
async def test_vk_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"user_id": "123", "message": "Test"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found in credentials" in result["response"]["description"]


@pytest.mark.asyncio
async def test_vk_execute_missing_access_token(integration, logger, bot_id):
    """Тест выполнения с отсутствующим access_token."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}  # Нет access_token
    })
    
    result = await integration.execute(
        config={"user_id": "123", "message": "Test"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "access_token not found" in result["response"]["description"]


@pytest.mark.asyncio
async def test_vk_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими параметрами."""
    result = await integration.execute(
        config={},  # Отсутствуют user_id и message
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "user_id and message are required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_vk_execute_missing_user_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без user_id."""
    result = await integration.execute(
        config={"message": "Test message"},  # Нет user_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_vk_execute_missing_message(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без message."""
    result = await integration.execute(
        config={"user_id": "123"},  # Нет message
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_vk_execute_vk_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибок VK API."""
    with patch('app.integrations.vk.send_message.vk_api') as mock_vk_api:
        # Создаем mock ошибки VK API
        from app.integrations.vk.send_message import VkApiError
        
        mock_vk_session = MagicMock()
        mock_vk = MagicMock()
        
        # Создаем ошибку с атрибутом code
        vk_error = VkApiError({"error_code": 7, "error_msg": "Permission denied"})
        mock_vk.messages.send = MagicMock(side_effect=vk_error)
        mock_vk_session.get_api.return_value = mock_vk
        mock_vk_api.VkApi.return_value = mock_vk_session
        mock_vk_api.exceptions.VkApiError = VkApiError
        
        result = await integration.execute(
            config={"user_id": "123", "message": "Test"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500  # или код ошибки VK


@pytest.mark.asyncio
async def test_vk_execute_invalid_user_id(integration, credentials_resolver, logger, bot_id):
    """Тест обработки невалидного user_id."""
    with patch('app.integrations.vk.send_message.vk_api') as mock_vk_api:
        mock_vk_session = MagicMock()
        mock_vk = MagicMock()
        
        # ValueError при конвертации user_id
        mock_vk.messages.send = MagicMock(side_effect=ValueError("Invalid user_id"))
        mock_vk_session.get_api.return_value = mock_vk
        mock_vk_api.VkApi.return_value = mock_vk_session
        
        result = await integration.execute(
            config={"user_id": "invalid", "message": "Test"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_vk_execute_library_not_available(integration, credentials_resolver, logger, bot_id):
    """Тест когда библиотека vk-api не установлена."""
    # Патчим VK_API_AVAILABLE на False
    with patch('app.integrations.vk.send_message.VK_API_AVAILABLE', False):
        result = await integration.execute(
            config={"user_id": "123", "message": "Test"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"]


@pytest.mark.asyncio
async def test_vk_execute_with_attachment(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения VK интеграции с вложением."""
    with patch('app.integrations.vk.send_message.vk_api') as mock_vk_api:
        mock_vk_session = MagicMock()
        mock_vk = MagicMock()
        mock_vk.messages.send = MagicMock(return_value=99999)
        mock_vk_session.get_api.return_value = mock_vk
        mock_vk_api.VkApi.return_value = mock_vk_session
        
        result = await integration.execute(
            config={
                "user_id": "123456",
                "message": "Смотри фото",
                "attachment": "photo-123456_789012"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["message_id"] == 99999


def test_vk_config_schema(integration):
    """Тест schema конфигурации."""
    metadata = integration.metadata
    schema = metadata.config_schema
    
    assert schema["type"] == "object"
    assert "user_id" in schema["required"]
    assert "message" in schema["required"]
    assert "user_id" in schema["properties"]
    assert "message" in schema["properties"]
    assert "keyboard" in schema["properties"]
    assert "attachment" in schema["properties"]
    assert "random_id" in schema["properties"]


def test_vk_examples(integration):
    """Тест примеров использования."""
    metadata = integration.metadata
    examples = metadata.examples
    
    assert len(examples) >= 1
    assert examples[0]["title"] == "Простое сообщение"
    assert "user_id" in examples[0]["config"]
    assert "message" in examples[0]["config"]
