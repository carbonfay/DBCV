"""Тесты для Telegram send_audio интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.telegram.send_audio import TelegramSendAudioIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    return TelegramSendAudioIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "bot_token": "123456:ABC-DEF-test-token"
    })
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_telegram_audio_metadata(integration):
    metadata = integration.metadata
    assert metadata.id == "telegram_send_audio"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Telegram Send Audio"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "telegram"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_telegram_send_audio_success(integration, credentials_resolver, logger, bot_id):
    with patch('app.integrations.telegram.send_audio.Bot') as mock_bot_class:
        mock_bot = MagicMock()
        mock_message = MagicMock()
        mock_message.message_id = 321
        mock_message.chat.id = 654
        mock_message.chat.type = "private"
        mock_message.audio.file_id = "audio-file-id"
        mock_message.caption = "Audio caption"
        mock_message.date = 1234567890

        mock_bot.send_audio = AsyncMock(return_value=mock_message)
        mock_bot_class.return_value = mock_bot

        result = await integration.execute(
            config={
                "chat_id": "123",
                "audio": "audio-file-id",
                "caption": "Here is audio"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["message_id"] == 321
        assert result["response"]["result"]["chat"]["id"] == 654
        assert result["response"]["result"]["audio"]["file_id"] == "audio-file-id"

        mock_bot.send_audio.assert_called_once()
        mock_bot_class.assert_called_once_with(token="123456:ABC-DEF-test-token")


@pytest.mark.asyncio
async def test_telegram_send_audio_no_credentials(integration, logger, bot_id):
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"chat_id": "123", "audio": "audio-file-id"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_telegram_send_audio_missing_config(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
