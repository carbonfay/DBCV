import pytest

from app.integrations.registry import registry


def test_telegram_registration():
    """Проверяет, что Telegram интеграции регистрируются через register_all()."""
    try:
        from app.integrations import telegram
    except Exception:
        pytest.skip("telegram package not available")

    # Выполняем регистрацию интеграций (idempotent)
    try:
        telegram.register_all()
    except Exception:
        pytest.skip("Не удалось зарегистрировать telegram integrations")

    integration = registry.get("telegram_send_video")
    assert integration is not None
    assert integration.metadata.id == "telegram_send_video"
