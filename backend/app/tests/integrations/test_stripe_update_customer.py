"""Тесты для Stripe Update Customer интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.stripe.update_customer import StripeUpdateCustomerIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Stripe Update Customer интеграции."""
    return StripeUpdateCustomerIntegration()


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


def test_stripe_update_customer_metadata(integration):
    """Тест метаданных Stripe Update Customer интеграции."""
    metadata = integration.metadata

    assert metadata.id == "stripe_update_customer"
    assert metadata.version == "1.0.0"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "stripe"
    assert metadata.credentials_strategy == "api_key"
    assert "customer_id" in metadata.config_schema["required"]


@pytest.mark.asyncio
async def test_stripe_update_customer_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного обновления клиента Stripe."""
    with patch("app.integrations.stripe.update_customer.stripe") as mock_stripe:
        mock_stripe.Customer.modify.return_value = {
            "id": "cus_ABC123",
            "email": "new@example.com",
            "name": "Jane Doe",
            "phone": None,
            "description": None,
            "metadata": {}
        }

        result = await integration.execute(
            config={"customer_id": "cus_ABC123", "email": "new@example.com", "name": "Jane Doe"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "cus_ABC123"
        assert result["response"]["result"]["email"] == "new@example.com"

        mock_stripe.Customer.modify.assert_called_once_with(
            "cus_ABC123",
            api_key="sk_test_123456789",
            email="new@example.com",
            name="Jane Doe"
        )


@pytest.mark.asyncio
async def test_stripe_update_customer_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"customer_id": "cus_ABC123", "email": "x@example.com"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_stripe_update_customer_missing_customer_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим customer_id."""
    result = await integration.execute(
        config={"email": "x@example.com"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_stripe_update_customer_no_fields_to_update(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без полей для обновления."""
    result = await integration.execute(
        config={"customer_id": "cus_ABC123"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
