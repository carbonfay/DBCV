"""Тесты для Stripe Refund интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.stripe.refund import StripeRefundIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Stripe Refund интеграции."""
    return StripeRefundIntegration()


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


def test_stripe_refund_metadata(integration):
    """Тест метаданных Stripe Refund интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "stripe_refund"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Stripe Refund"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "stripe"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_stripe_refund_execute_success_full_refund(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения полного возврата."""
    with patch('app.integrations.stripe.refund.stripe') as mock_stripe:
        # Настраиваем mock
        mock_refund = MagicMock()
        mock_refund.id = "re_1234567890"
        mock_refund.status = "succeeded"
        mock_refund.amount = 1000
        mock_refund.currency = "usd"
        mock_refund.charge = "ch_1234567890"
        mock_refund.created = 1234567890
        mock_refund.reason = None
        
        mock_stripe.Refund.create = MagicMock(return_value=mock_refund)
        mock_stripe.api_key = None
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "charge_id": "ch_1234567890"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "re_1234567890"
        assert result["response"]["result"]["status"] == "succeeded"
        assert result["response"]["result"]["amount"] == 1000
        assert result["response"]["result"]["currency"] == "usd"
        
        # Проверяем, что API ключ был установлен
        assert mock_stripe.api_key == "sk_test_1234567890abcdef"
        
        # Проверяем, что метод библиотеки был вызван
        mock_stripe.Refund.create.assert_called_once()
        call_args = mock_stripe.Refund.create.call_args[1]
        assert call_args["charge"] == "ch_1234567890"


@pytest.mark.asyncio
async def test_stripe_refund_execute_success_partial_refund(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения частичного возврата."""
    with patch('app.integrations.stripe.refund.stripe') as mock_stripe:
        # Настраиваем mock
        mock_refund = MagicMock()
        mock_refund.id = "re_1234567890"
        mock_refund.status = "succeeded"
        mock_refund.amount = 500
        mock_refund.currency = "usd"
        mock_refund.charge = "ch_1234567890"
        mock_refund.created = 1234567890
        mock_refund.reason = "requested_by_customer"
        
        mock_stripe.Refund.create = MagicMock(return_value=mock_refund)
        mock_stripe.api_key = None
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "charge_id": "ch_1234567890",
                "amount": 500,
                "reason": "requested_by_customer"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "re_1234567890"
        assert result["response"]["result"]["status"] == "succeeded"
        assert result["response"]["result"]["amount"] == 500
        assert result["response"]["result"]["reason"] == "requested_by_customer"
        
        # Проверяем, что метод библиотеки был вызван с правильными параметрами
        mock_stripe.Refund.create.assert_called_once()
        call_args = mock_stripe.Refund.create.call_args[1]
        assert call_args["charge"] == "ch_1234567890"
        assert call_args["amount"] == 500
        assert call_args["reason"] == "requested_by_customer"


@pytest.mark.asyncio
async def test_stripe_refund_execute_payment_intent(integration, credentials_resolver, logger, bot_id):
    """Тест возврата по payment intent ID."""
    with patch('app.integrations.stripe.refund.stripe') as mock_stripe:
        # Настраиваем mock
        mock_refund = MagicMock()
        mock_refund.id = "re_1234567890"
        mock_refund.status = "succeeded"
        mock_refund.amount = 1000
        mock_refund.currency = "usd"
        mock_refund.charge = "ch_1234567890"
        mock_refund.created = 1234567890
        mock_refund.reason = None
        
        mock_stripe.Refund.create = MagicMock(return_value=mock_refund)
        mock_stripe.api_key = None
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "charge_id": "pi_1234567890"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "re_1234567890"
        
        # Проверяем, что метод библиотеки был вызван с payment_intent
        mock_stripe.Refund.create.assert_called_once()
        call_args = mock_stripe.Refund.create.call_args[1]
        assert call_args["payment_intent"] == "pi_1234567890"


@pytest.mark.asyncio
async def test_stripe_refund_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"charge_id": "ch_1234567890"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_refund_execute_missing_api_key(integration, logger, bot_id):
    """Тест выполнения с отсутствующим api_key в credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "wrong_key": "value"
        }
    })
    
    result = await integration.execute(
        config={"charge_id": "ch_1234567890"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "api_key" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_refund_execute_missing_charge_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим charge_id."""
    result = await integration.execute(
        config={},  # Отсутствует charge_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "charge_id" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_stripe_refund_execute_stripe_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки Stripe API."""
    with patch('app.integrations.stripe.refund.stripe') as mock_stripe:
        # Настраиваем mock для ошибки
        from stripe.error import StripeError
        
        mock_error = StripeError()
        mock_error.http_status = 402
        mock_error.user_message = "Payment required"
        mock_stripe.Refund.create = MagicMock(side_effect=mock_error)
        mock_stripe.api_key = None
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "charge_id": "ch_1234567890"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 402


@pytest.mark.asyncio
async def test_stripe_refund_execute_with_metadata(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с метаданными."""
    with patch('app.integrations.stripe.refund.stripe') as mock_stripe:
        # Настраиваем mock
        mock_refund = MagicMock()
        mock_refund.id = "re_1234567890"
        mock_refund.status = "succeeded"
        mock_refund.amount = 1000
        mock_refund.currency = "usd"
        mock_refund.charge = "ch_1234567890"
        mock_refund.created = 1234567890
        mock_refund.reason = None
        
        mock_stripe.Refund.create = MagicMock(return_value=mock_refund)
        mock_stripe.api_key = None
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "charge_id": "ch_1234567890",
                "metadata": {
                    "order_id": "12345",
                    "reason": "customer_request"
                }
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        
        # Проверяем, что метод библиотеки был вызван с метаданными
        mock_stripe.Refund.create.assert_called_once()
        call_args = mock_stripe.Refund.create.call_args[1]
        assert call_args["charge"] == "ch_1234567890"
        assert call_args["metadata"] == {"order_id": "12345", "reason": "customer_request"}


@pytest.mark.asyncio
async def test_stripe_refund_execute_library_not_available(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения когда библиотека stripe не установлена."""
    # Мокаем модуль, чтобы STRIPE_AVAILABLE был False
    with patch('app.integrations.stripe.refund.STRIPE_AVAILABLE', False):
        result = await integration.execute(
            config={"charge_id": "ch_1234567890"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"].lower()

