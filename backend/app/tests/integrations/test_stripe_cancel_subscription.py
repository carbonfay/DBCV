"""Тесты для Stripe Cancel Subscription интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.stripe.cancel_subscription import StripeCancelSubscriptionIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Stripe Cancel Subscription интеграции."""
    return StripeCancelSubscriptionIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver с тестовым Stripe api_key."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {"api_key": "sk_test_123456789"}
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


def test_stripe_cancel_subscription_metadata(integration):
    """Тест метаданных Stripe Cancel Subscription интеграции."""
    metadata = integration.metadata

    assert metadata.id == "stripe_cancel_subscription"
    assert metadata.category == "payments"
    assert metadata.config_schema["required"] == ["subscription_id"]


@pytest.mark.asyncio
async def test_stripe_cancel_subscription_immediate_cancel(integration, credentials_resolver, logger, bot_id):
    """Тест немедленной отмены подписки."""
    with patch("app.integrations.stripe.cancel_subscription.stripe") as mock_stripe:
        mock_stripe.Subscription.delete.return_value = {
            "id": "sub_ABC123",
            "status": "canceled",
            "cancel_at_period_end": False,
            "canceled_at": 1735689600,
            "current_period_end": 1735689600
        }

        result = await integration.execute(
            config={"subscription_id": "sub_ABC123"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["status"] == "canceled"
        mock_stripe.Subscription.delete.assert_called_once_with(
            "sub_ABC123", api_key="sk_test_123456789"
        )
        mock_stripe.Subscription.modify.assert_not_called()


@pytest.mark.asyncio
async def test_stripe_cancel_subscription_at_period_end(integration, credentials_resolver, logger, bot_id):
    """Тест отмены подписки в конце оплаченного периода."""
    with patch("app.integrations.stripe.cancel_subscription.stripe") as mock_stripe:
        mock_stripe.Subscription.modify.return_value = {
            "id": "sub_ABC123",
            "status": "active",
            "cancel_at_period_end": True,
            "canceled_at": None,
            "current_period_end": 1735689600
        }

        result = await integration.execute(
            config={"subscription_id": "sub_ABC123", "at_period_end": True, "cancellation_reason": "too expensive"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["cancel_at_period_end"] is True
        mock_stripe.Subscription.modify.assert_called_once_with(
            "sub_ABC123",
            api_key="sk_test_123456789",
            cancel_at_period_end=True,
            cancellation_details={"comment": "too expensive"}
        )
        mock_stripe.Subscription.delete.assert_not_called()


@pytest.mark.asyncio
async def test_stripe_cancel_subscription_missing_subscription_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим subscription_id."""
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_stripe_cancel_subscription_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"subscription_id": "sub_ABC123"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
