"""Тесты для VK интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.vk.send_message import (
    VkSendMessageIntegration,
    VK_API_VERSION,
    VK_API_URL,
    VK_HTTP_TIMEOUT,
)
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
            "access_token": "vk-test-token"
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


def test_vk_metadata(integration):
    """Тест метаданных VK интеграции."""
    metadata = integration.metadata

    assert metadata.id == "vk_send_message"
    assert metadata.version == "1.0.0"
    assert metadata.name == "VK Send Message"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "vk"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_vk_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения VK интеграции."""
    with patch("app.integrations.vk.send_message.HTTPX_AVAILABLE", True), \
         patch("app.integrations.vk.send_message.httpx") as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": 321}
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        mock_httpx.AsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx.AsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await integration.execute(
            config={
                "peer_id": "123",
                "message": "Test message",
                "random_id": 42
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["message_id"] == 321
        assert result["response"]["result"]["peer_id"] == 123
        assert result["response"]["result"]["random_id"] == 42

        mock_httpx.AsyncClient.assert_called_once_with(timeout=VK_HTTP_TIMEOUT)
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == VK_API_URL
        assert kwargs["data"]["access_token"] == "vk-test-token"
        assert kwargs["data"]["v"] == VK_API_VERSION


@pytest.mark.asyncio
async def test_vk_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    with patch("app.integrations.vk.send_message.HTTPX_AVAILABLE", True):
        result = await integration.execute(
            config={"peer_id": "123", "message": "Test"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_vk_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими параметрами."""
    with patch("app.integrations.vk.send_message.HTTPX_AVAILABLE", True):
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
