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
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "sk_test_1234567890abcdef"
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


def test_stripe_metadata(integration):
    """Тест метаданных Stripe интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "stripe_cancel_subscription"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Stripe Cancel Subscription"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "stripe"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "stripe>=7.0.0"
    
    # Проверяем config_schema
    assert "subscription_id" in metadata.config_schema["properties"]
    assert "subscription_id" in metadata.config_schema["required"]


@pytest.mark.asyncio
async def test_stripe_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Stripe интеграции."""
    with patch('app.integrations.stripe.cancel_subscription.stripe') as mock_stripe:
        # Настраиваем mock
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_1234567890"
        mock_subscription.status = "canceled"
        
        mock_stripe.api_key = None
        mock_stripe.Subscription.cancel = MagicMock(return_value=mock_subscription)
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "subscription_id": "sub_1234567890"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "sub_1234567890"
        assert result["response"]["result"]["status"] == "canceled"
        
        # Проверяем, что метод библиотеки был вызван
        mock_stripe.Subscription.cancel.assert_called_once_with("sub_1234567890")
        assert mock_stripe.api_key == "sk_test_1234567890abcdef"


@pytest.mark.asyncio
async def test_stripe_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"subscription_id": "sub_1234567890"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_missing_api_key(integration, logger, bot_id):
    """Тест выполнения с credentials без api_key."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}
    })
    
    result = await integration.execute(
        config={"subscription_id": "sub_1234567890"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api_key" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_missing_subscription_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим subscription_id."""
    result = await integration.execute(
        config={},  # Отсутствует subscription_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "subscription_id" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_stripe_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки Stripe API."""
    # Создаем класс исключения для мокирования
    class MockStripeError(Exception):
        def __init__(self, message, http_status=404):
            self.http_status = http_status
            self.message = message
            super().__init__(message)
    
    with patch('app.integrations.stripe.cancel_subscription.stripe') as mock_stripe, \
         patch('app.integrations.stripe.cancel_subscription.StripeError', MockStripeError):
        # Настраиваем mock для ошибки
        mock_stripe.api_key = None
        mock_stripe_error = MockStripeError("No such subscription: sub_invalid", http_status=404)
        mock_stripe.Subscription.cancel = MagicMock(side_effect=mock_stripe_error)
        
        result = await integration.execute(
            config={
                "subscription_id": "sub_invalid"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "subscription" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_credentials_backward_compatibility(integration, logger, bot_id):
    """Тест обратной совместимости credentials (данные в корне, не в payload)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "api_key": "sk_test_backward_compat"
    })
    
    with patch('app.integrations.stripe.cancel_subscription.stripe') as mock_stripe:
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_1234567890"
        mock_subscription.status = "canceled"
        mock_stripe.api_key = None
        mock_stripe.Subscription.cancel = MagicMock(return_value=mock_subscription)
        
        result = await integration.execute(
            config={"subscription_id": "sub_1234567890"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert mock_stripe.api_key == "sk_test_backward_compat"

