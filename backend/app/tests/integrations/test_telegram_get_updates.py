import pytest

from app.integrations.telegram.get_updates import TelegramGetUpdatesIntegration


@pytest.mark.asyncio
async def test_telegram_get_updates_basic():
    """Простейшая проверка: класс доступен, метаданные и execute присутствуют."""
    integration = TelegramGetUpdatesIntegration()

    # Метаданные
    meta = integration.metadata
    assert meta.id == "telegram_get_updates"
    assert meta.category == "messaging"

    # execute должен быть корутиной/вызываемым
    assert callable(getattr(integration, "execute", None))
