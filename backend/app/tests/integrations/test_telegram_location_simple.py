"""Простой тест для Telegram Send Location интеграции."""
from app.integrations.telegram.send_location import TelegramSendLocationIntegration


def test_telegram_location_metadata():
    """Тест метаданных Telegram Send Location интеграции."""
    integration = TelegramSendLocationIntegration()
    metadata = integration.metadata
    
    assert metadata.id == "telegram_send_location"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Telegram Send Location"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "telegram"
    assert metadata.credentials_strategy == "api_key"