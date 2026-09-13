"""Тесты для Stripe Create Subscription интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.stripe.create_subscription import StripeCreateSubscriptionIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Stripe Create Subscription интеграции."""
    return StripeCreateSubscriptionIntegration()


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


def test_stripe_create_subscription_metadata(integration):
    """Тест метаданных Stripe Create Subscription интеграции."""
    metadata = integration.metadata

    assert metadata.id == "stripe_create_subscription"
    assert metadata.category == "payments"
    assert set(metadata.config_schema["required"]) == {"customer_id", "items"}


@pytest.mark.asyncio
async def test_stripe_create_subscription_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного создания подписки в Stripe."""
    with patch("app.integrations.stripe.create_subscription.stripe") as mock_stripe:
        mock_stripe.Subscription.create.return_value = {
            "id": "sub_ABC123",
            "status": "active",
            "customer": "cus_ABC123",
            "current_period_end": 1735689600,
            "trial_end": None,
            "latest_invoice": "in_123",
            "items": {"data": [{"id": "si_1"}]}
        }

        result = await integration.execute(
            config={
                "customer_id": "cus_ABC123",
                "items": [{"price": "price_123", "quantity": 1}],
                "trial_period_days": 7
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "sub_ABC123"
        assert result["response"]["result"]["items_count"] == 1

        mock_stripe.Subscription.create.assert_called_once_with(
            customer="cus_ABC123",
            items=[{"price": "price_123", "quantity": 1}],
            api_key="sk_test_123456789",
            trial_period_days=7
        )


@pytest.mark.asyncio
async def test_stripe_create_subscription_missing_items(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с пустым списком items."""
    result = await integration.execute(
        config={"customer_id": "cus_ABC123", "items": []},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_stripe_create_subscription_automatic_tax(integration, credentials_resolver, logger, bot_id):
    """Тест включения автоматического расчёта налогов."""
    with patch("app.integrations.stripe.create_subscription.stripe") as mock_stripe:
        mock_stripe.Subscription.create.return_value = {
            "id": "sub_ABC123",
            "status": "active",
            "customer": "cus_ABC123",
            "items": {"data": []}
        }

        await integration.execute(
            config={
                "customer_id": "cus_ABC123",
                "items": [{"price": "price_123"}],
                "automatic_tax": True
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        _, kwargs = mock_stripe.Subscription.create.call_args
        assert kwargs["automatic_tax"] == {"enabled": True}
        assert kwargs["items"] == [{"price": "price_123"}]


@pytest.mark.asyncio
async def test_stripe_create_subscription_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"customer_id": "cus_ABC123", "items": [{"price": "price_123"}]},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
