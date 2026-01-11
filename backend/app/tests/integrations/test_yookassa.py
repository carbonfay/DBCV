"""Тесты для YooKassa Create Refund интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime

from app.integrations.yookassa.create_refund import YooKassaCreateRefundIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр YooKassa интеграции."""
    return YooKassaCreateRefundIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "shop_id": "test_shop_id",
            "secret_key": "test_secret_key"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_without_payload():
    """Создает mock credentials resolver без payload (обратная совместимость)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "shopId": "test_shop_id",
        "secretKey": "test_secret_key"
    })
    return resolver


@pytest.fixture
def credentials_resolver_with_account_id():
    """Создает mock credentials resolver с account_id (альтернативный формат)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "account_id": "test_shop_id",
            "secret_key": "test_secret_key"
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


@pytest.fixture
def mock_refund():
    """Создает mock объект refund от yookassa."""
    refund = Mock()
    refund.id = "216749f7-0016-50be-b000-078d43a63ae4"
    refund.status = "succeeded"
    refund.payment_id = "21740069-000f-50be-b000-0486ffbf45b0"
    refund.created_at = datetime(2017, 10, 4, 19, 27, 51)
    
    # Mock для amount
    amount = Mock()
    amount.value = "100.00"
    amount.currency = "RUB"
    refund.amount = amount
    
    # Опциональные поля
    refund.description = None
    refund.refund_authorization_details = None
    refund.metadata = {}
    
    return refund


def test_yookassa_metadata(integration):
    """Тест метаданных YooKassa интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "yookassa_create_refund"
    assert metadata.version == "1.0.0"
    assert metadata.name == "YooKassa Create Refund"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "yookassa"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.icon_s3_key == "icons/integrations/yookassa.svg"
    assert metadata.color == "#FFDB4D"
    assert "payment_id" in metadata.config_schema["required"]
    assert "amount" in metadata.config_schema["required"]
    assert metadata.examples is not None
    assert len(metadata.examples) > 0


@pytest.mark.asyncio
async def test_yookassa_execute_success(integration, credentials_resolver, logger, bot_id, mock_refund):
    """Тест успешного выполнения YooKassa интеграции."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        # Настраиваем mock для Refund.create
        mock_refund_class.create.return_value = mock_refund
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {
                    "value": "100.00",
                    "currency": "RUB"
                },
                "description": "Test refund"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == mock_refund.id
        assert result["response"]["result"]["status"] == mock_refund.status
        assert result["response"]["result"]["payment_id"] == mock_refund.payment_id
        assert result["response"]["result"]["amount"]["value"] == "100.00"
        assert result["response"]["result"]["amount"]["currency"] == "RUB"
        
        # Проверяем, что Configuration был настроен
        assert mock_config.account_id == "test_shop_id"
        assert mock_config.secret_key == "test_secret_key"
        
        # Проверяем, что Refund.create был вызван
        mock_refund_class.create.assert_called_once()


@pytest.mark.asyncio
async def test_yookassa_execute_success_partial_refund(integration, credentials_resolver, logger, bot_id, mock_refund):
    """Тест успешного частичного возврата."""
    # Модифицируем mock для частичного возврата
    amount = Mock()
    amount.value = "50.00"
    amount.currency = "RUB"
    mock_refund.amount = amount
    
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.return_value = mock_refund
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {
                    "value": "50.00",
                    "currency": "RUB"
                }
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["amount"]["value"] == "50.00"
        mock_refund_class.create.assert_called_once()


@pytest.mark.asyncio
async def test_yookassa_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
            "amount": {"value": "100.00", "currency": "RUB"}
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yookassa_execute_missing_shop_credentials(integration, logger, bot_id):
    """Тест выполнения с отсутствующими shop_id или secret_key."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}  # Пустой payload
    })
    
    result = await integration.execute(
        config={
            "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
            "amount": {"value": "100.00", "currency": "RUB"}
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "shop_id and secret_key" in result["response"]["description"]


@pytest.mark.asyncio
async def test_yookassa_execute_missing_payment_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим payment_id."""
    result = await integration.execute(
        config={
            "amount": {"value": "100.00", "currency": "RUB"}
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "payment_id is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_yookassa_execute_missing_amount(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим amount."""
    result = await integration.execute(
        config={
            "payment_id": "21740069-000f-50be-b000-0486ffbf45b0"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "amount is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_yookassa_execute_missing_amount_value(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим amount.value."""
    result = await integration.execute(
        config={
            "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
            "amount": {"currency": "RUB"}
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "amount.value is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_yookassa_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки API YooKassa."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        # Симулируем ошибку API
        mock_refund_class.create.side_effect = Exception("Payment not found")
        
        result = await integration.execute(
            config={
                "payment_id": "invalid_payment_id",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yookassa_execute_unauthorized_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки 401 Unauthorized."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.side_effect = Exception("Unauthorized: Invalid credentials")
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "unauthorized" in result["response"]["description"].lower() or "credentials" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yookassa_execute_forbidden_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки 403 Forbidden."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.side_effect = Exception("Forbidden: Access denied")
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 403


@pytest.mark.asyncio
async def test_yookassa_execute_bad_request_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки 400 Bad Request."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.side_effect = Exception("Bad Request: Invalid amount")
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "-100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_yookassa_execute_rate_limit_error(integration, credentials_resolver, logger, bot_id):
    """Тест ошибки 429 Rate Limit."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.side_effect = Exception("429 Rate limit exceeded")
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 429


@pytest.mark.asyncio
async def test_yookassa_execute_credentials_without_payload(integration, credentials_resolver_without_payload, logger, bot_id, mock_refund):
    """Тест с credentials без payload (обратная совместимость)."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.return_value = mock_refund
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver_without_payload,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        # Проверяем, что использовались правильные credentials
        assert mock_config.account_id == "test_shop_id"
        assert mock_config.secret_key == "test_secret_key"


@pytest.mark.asyncio
async def test_yookassa_execute_credentials_with_account_id(integration, credentials_resolver_with_account_id, logger, bot_id, mock_refund):
    """Тест с credentials с account_id (альтернативный формат)."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.return_value = mock_refund
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver_with_account_id,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert mock_config.account_id == "test_shop_id"
        assert mock_config.secret_key == "test_secret_key"


@pytest.mark.asyncio
async def test_yookassa_execute_yookassa_not_available(integration, credentials_resolver, logger, bot_id):
    """Тест случая, когда библиотека yookassa не установлена."""
    with patch('app.integrations.yookassa.create_refund.YOOKASSA_AVAILABLE', False):
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "yookassa" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yookassa_execute_with_description(integration, credentials_resolver, logger, bot_id, mock_refund):
    """Тест создания возврата с описанием."""
    mock_refund.description = "Test refund description"
    
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.return_value = mock_refund
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"},
                "description": "Test refund description"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["description"] == "Test refund description"
        
        # Проверяем, что description был передан в Refund.create
        call_args = mock_refund_class.create.call_args[0][0]
        assert call_args["description"] == "Test refund description"


@pytest.mark.asyncio
async def test_yookassa_execute_without_description(integration, credentials_resolver, logger, bot_id, mock_refund):
    """Тест создания возврата без описания."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.return_value = mock_refund
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        
        # Проверяем, что description не был передан в Refund.create
        call_args = mock_refund_class.create.call_args[0][0]
        assert "description" not in call_args


@pytest.mark.asyncio
async def test_yookassa_execute_default_currency(integration, credentials_resolver, logger, bot_id, mock_refund):
    """Тест использования валюты по умолчанию (RUB)."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.return_value = mock_refund
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        
        # Проверяем, что использовалась валюта RUB по умолчанию
        call_args = mock_refund_class.create.call_args[0][0]
        assert call_args["amount"]["currency"] == "RUB"


@pytest.mark.asyncio
async def test_yookassa_execute_different_currencies(integration, credentials_resolver, logger, bot_id):
    """Тест с различными валютами."""
    currencies = ["RUB", "USD", "EUR"]
    
    for currency in currencies:
        mock_refund = Mock()
        mock_refund.id = "test-refund-id"
        mock_refund.status = "succeeded"
        mock_refund.payment_id = "21740069-000f-50be-b000-0486ffbf45b0"
        mock_refund.created_at = datetime(2017, 10, 4, 19, 27, 51)
        
        amount = Mock()
        amount.value = "100.00"
        amount.currency = currency
        mock_refund.amount = amount
        
        with patch('app.integrations.yookassa.create_refund.Configuration'), \
             patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
            
            mock_refund_class.create.return_value = mock_refund
            
            result = await integration.execute(
                config={
                    "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                    "amount": {"value": "100.00", "currency": currency}
                },
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger
            )
            
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["amount"]["currency"] == currency


@pytest.mark.asyncio
async def test_yookassa_execute_full_refund_data(integration, credentials_resolver, logger, bot_id):
    """Тест с полными данными возврата (включая опциональные поля)."""
    mock_refund = Mock()
    mock_refund.id = "216749f7-0016-50be-b000-078d43a63ae4"
    mock_refund.status = "succeeded"
    mock_refund.payment_id = "21740069-000f-50be-b000-0486ffbf45b0"
    mock_refund.created_at = datetime(2017, 10, 4, 19, 27, 51)
    mock_refund.description = "Full refund"
    
    amount = Mock()
    amount.value = "100.00"
    amount.currency = "RUB"
    mock_refund.amount = amount
    
    # Mock для refund_authorization_details
    auth_details = Mock()
    auth_details.rrn = "603668680243"
    mock_refund.refund_authorization_details = auth_details
    
    # Mock для metadata
    mock_refund.metadata = {"order_id": "12345"}
    
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.return_value = mock_refund
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"},
                "description": "Full refund"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == mock_refund.id
        assert result["response"]["result"]["status"] == mock_refund.status
        assert result["response"]["result"]["description"] == "Full refund"
        assert "refund_authorization_details" in result["response"]["result"]
        assert result["response"]["result"]["refund_authorization_details"]["rrn"] == "603668680243"
        assert "metadata" in result["response"]["result"]


@pytest.mark.asyncio
async def test_yookassa_execute_generic_exception(integration, credentials_resolver, logger, bot_id):
    """Тест обработки общего исключения."""
    with patch('app.integrations.yookassa.create_refund.Configuration') as mock_config, \
         patch('app.integrations.yookassa.create_refund.Refund') as mock_refund_class:
        
        mock_refund_class.create.side_effect = Exception("Unexpected error occurred")
        
        result = await integration.execute(
            config={
                "payment_id": "21740069-000f-50be-b000-0486ffbf45b0",
                "amount": {"value": "100.00", "currency": "RUB"}
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "Unexpected error" in result["response"]["description"]
        
        # Проверяем, что ошибка была залогирована
        logger.error.assert_called()
