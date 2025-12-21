"""Тесты для Stripe Get Payment интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.stripe.get_payment import StripeGetPaymentIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Stripe интеграции."""
    return StripeGetPaymentIntegration()


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
    
    assert metadata.id == "stripe_get_payment"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Stripe Get Payment"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "stripe"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_stripe_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Stripe интеграции."""
    with patch('app.integrations.stripe.get_payment.stripe') as mock_stripe:
        # Настраиваем mock PaymentIntent
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_1234567890abcdef"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.description = "Test payment"
        
        # Настраиваем mock stripe.PaymentIntent.retrieve
        mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent
        mock_stripe.api_key = None  # Изначально не установлен
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "payment_id": "pi_1234567890abcdef"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "pi_1234567890abcdef"
        assert result["response"]["result"]["status"] == "succeeded"
        assert result["response"]["result"]["amount"] == 1000
        assert result["response"]["result"]["currency"] == "usd"
        assert result["response"]["result"]["description"] == "Test payment"
        
        # Проверяем, что API ключ был установлен
        assert mock_stripe.api_key == "sk_test_1234567890abcdef"
        
        # Проверяем, что метод библиотеки был вызван
        mock_stripe.PaymentIntent.retrieve.assert_called_once_with("pi_1234567890abcdef")


@pytest.mark.asyncio
async def test_stripe_execute_success_no_description(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения без описания."""
    with patch('app.integrations.stripe.get_payment.stripe') as mock_stripe:
        # Настраиваем mock PaymentIntent без description
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_1234567890abcdef"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 2000
        mock_payment_intent.currency = "rub"
        del mock_payment_intent.description  # Удаляем атрибут description
        
        mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent
        
        result = await integration.execute(
            config={
                "payment_id": "pi_1234567890abcdef"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "pi_1234567890abcdef"
        assert result["response"]["result"]["status"] == "succeeded"
        assert result["response"]["result"]["amount"] == 2000
        assert result["response"]["result"]["currency"] == "rub"
        assert result["response"]["result"]["description"] is None


@pytest.mark.asyncio
async def test_stripe_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"payment_id": "pi_1234567890abcdef"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_missing_api_key_in_payload(integration, logger, bot_id):
    """Тест выполнения с отсутствующим api_key в payload."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "wrong_key": "some_value"
        }
    })
    
    result = await integration.execute(
        config={"payment_id": "pi_1234567890abcdef"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api_key" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_missing_payment_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим payment_id."""
    result = await integration.execute(
        config={},  # Отсутствует payment_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "payment_id" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_execute_stripe_error(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с ошибкой Stripe API."""
    with patch('app.integrations.stripe.get_payment.stripe') as mock_stripe:
        # Создаем mock ошибку Stripe
        mock_error = Exception("No such payment_intent: pi_invalid")
        mock_error.http_status = 404  # type: ignore
        
        mock_stripe.PaymentIntent.retrieve.side_effect = mock_error
        
        result = await integration.execute(
            config={
                "payment_id": "pi_invalid"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "pi_invalid" in result["response"]["description"]


@pytest.mark.asyncio
async def test_stripe_execute_stripe_error_no_http_status(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с ошибкой Stripe без http_status."""
    with patch('app.integrations.stripe.get_payment.stripe') as mock_stripe:
        # Создаем mock ошибку Stripe без http_status
        mock_error = Exception("Unexpected error")
        # Не устанавливаем http_status
        
        mock_stripe.PaymentIntent.retrieve.side_effect = mock_error
        
        result = await integration.execute(
            config={
                "payment_id": "pi_test"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500  # Дефолтный код ошибки
        assert "Unexpected error" in result["response"]["description"]


@pytest.mark.asyncio
async def test_stripe_execute_unexpected_error(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с неожиданной ошибкой."""
    with patch('app.integrations.stripe.get_payment.stripe') as mock_stripe:
        # Создаем неожиданную ошибку (не StripeError)
        mock_stripe.PaymentIntent.retrieve.side_effect = ValueError("Unexpected error")
        
        result = await integration.execute(
            config={
                "payment_id": "pi_test"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "Unexpected error" in result["response"]["description"]


@pytest.mark.asyncio
async def test_stripe_execute_credentials_without_payload(integration, logger, bot_id):
    """Тест выполнения с credentials без payload (обратная совместимость)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "api_key": "sk_test_1234567890abcdef"  # api_key в корне, не в payload
    })
    
    with patch('app.integrations.stripe.get_payment.stripe') as mock_stripe:
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.description = None
        
        mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent
        
        result = await integration.execute(
            config={
                "payment_id": "pi_test"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert mock_stripe.api_key == "sk_test_1234567890abcdef"

