"""Тесты для Stripe Create Payment Intent интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.stripe.create_payment_intent import StripeCreatePaymentIntentIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Stripe интеграции."""
    return StripeCreatePaymentIntentIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "sk_test_1234567890"
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
    
    assert metadata.id == "stripe_create_payment_intent"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Stripe Create Payment Intent"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "stripe"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_stripe_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Stripe интеграции."""
    with patch('app.integrations.stripe.create_payment_intent.stripe') as mock_stripe:
        # Настраиваем mock PaymentIntent
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_1234567890"
        mock_payment_intent.status = "requires_payment_method"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.client_secret = "pi_test_1234567890_secret_abc123"
        mock_payment_intent.description = None
        mock_payment_intent.metadata = {}
        mock_payment_intent.customer = None
        mock_payment_intent.payment_method = None
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        mock_stripe.api_key = None
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "amount": 1000,
                "currency": "usd"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "pi_test_1234567890"
        assert result["response"]["result"]["status"] == "requires_payment_method"
        assert result["response"]["result"]["amount"] == 1000
        assert result["response"]["result"]["currency"] == "usd"
        assert "client_secret" in result["response"]["result"]
        assert "next_action" in result["response"]["result"]
        
        # Проверяем, что метод библиотеки был вызван
        mock_stripe.PaymentIntent.create.assert_called_once()
        call_args = mock_stripe.PaymentIntent.create.call_args[1]
        assert call_args["amount"] == 1000
        assert call_args["currency"] == "usd"
        assert "automatic_payment_methods" in call_args
        assert call_args["automatic_payment_methods"]["enabled"] is True
        assert mock_stripe.api_key == "sk_test_1234567890"


@pytest.mark.asyncio
async def test_stripe_execute_with_payment_method(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с указанным payment_method."""
    with patch('app.integrations.stripe.create_payment_intent.stripe') as mock_stripe:
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_1234567890"
        mock_payment_intent.status = "requires_confirmation"
        mock_payment_intent.amount = 2000
        mock_payment_intent.currency = "rub"
        mock_payment_intent.client_secret = "pi_test_1234567890_secret_abc123"
        mock_payment_intent.description = None
        mock_payment_intent.metadata = {}
        mock_payment_intent.customer = None
        mock_payment_intent.payment_method = "pm_test_123"
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        
        result = await integration.execute(
            config={
                "amount": 2000,
                "currency": "rub",
                "payment_method": "pm_test_123"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        call_args = mock_stripe.PaymentIntent.create.call_args[1]
        assert call_args["payment_method"] == "pm_test_123"
        assert "automatic_payment_methods" not in call_args


@pytest.mark.asyncio
async def test_stripe_execute_with_all_params(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения со всеми параметрами."""
    with patch('app.integrations.stripe.create_payment_intent.stripe') as mock_stripe:
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_1234567890"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 5000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.client_secret = "pi_test_1234567890_secret_abc123"
        mock_payment_intent.description = "Test payment"
        mock_payment_intent.metadata = {"order_id": "12345"}
        mock_payment_intent.customer = "cus_test_123"
        mock_payment_intent.payment_method = "pm_test_123"
        
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        
        result = await integration.execute(
            config={
                "amount": 5000,
                "currency": "usd",
                "payment_method": "pm_test_123",
                "customer": "cus_test_123",
                "description": "Test payment",
                "metadata": {"order_id": "12345"},
                "receipt_email": "test@example.com",
                "capture_method": "manual",
                "confirm": True
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["status"] == "succeeded"
        assert result["response"]["result"]["description"] == "Test payment"
        assert result["response"]["result"]["metadata"] == {"order_id": "12345"}
        assert result["response"]["result"]["customer"] == "cus_test_123"
        assert result["response"]["result"]["payment_method"] == "pm_test_123"
        
        call_args = mock_stripe.PaymentIntent.create.call_args[1]
        assert call_args["amount"] == 5000
        assert call_args["currency"] == "usd"
        assert call_args["payment_method"] == "pm_test_123"
        assert call_args["customer"] == "cus_test_123"
        assert call_args["description"] == "Test payment"
        assert call_args["metadata"] == {"order_id": "12345"}
        assert call_args["receipt_email"] == "test@example.com"
        assert call_args["capture_method"] == "manual"
        assert call_args["confirm"] is True


@pytest.mark.asyncio
async def test_stripe_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"amount": 1000, "currency": "usd"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_missing_api_key(integration, logger, bot_id):
    """Тест выполнения без api_key в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}
    })
    
    result = await integration.execute(
        config={"amount": 1000, "currency": "usd"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api_key" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими обязательными параметрами."""
    result = await integration.execute(
        config={},  # Отсутствуют amount и currency
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "required" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_stripe_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки Stripe."""
    with patch('app.integrations.stripe.create_payment_intent.stripe') as mock_stripe:
        from stripe import StripeError
        
        # Создаем реальную ошибку StripeError
        class TestStripeError(StripeError):
            def __init__(self):
                super().__init__("Your card was declined.")
                self.http_status = 402
        
        mock_error = TestStripeError()
        mock_stripe.PaymentIntent.create.side_effect = mock_error
        
        result = await integration.execute(
            config={
                "amount": 1000,
                "currency": "usd"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 402
        assert "declined" in result["response"]["description"].lower() or "error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_library_not_available(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения когда библиотека stripe не доступна."""
    # Временно заменяем STRIPE_AVAILABLE
    original_available = integration.__class__.__module__
    with patch('app.integrations.stripe.create_payment_intent.STRIPE_AVAILABLE', False):
        # Пересоздаем интеграцию для применения изменений
        integration = StripeCreatePaymentIntentIntegration()
        
        result = await integration.execute(
            config={"amount": 1000, "currency": "usd"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"].lower()

