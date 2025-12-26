"""Тесты для PayPal Create Payout интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from app.integrations.paypal.create_payout import PayPalCreatePayoutIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр PayPal интеграции."""
    return PayPalCreatePayoutIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "client_id": "test-client-id-12345",
            "client_secret": "test-client-secret-67890"
        }
    })
    return resolver


@pytest.fixture
def credentials_resolver_no_payload():
    """Создает mock credentials resolver без payload (обратная совместимость)."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "client_id": "test-client-id-12345",
        "client_secret": "test-client-secret-67890"
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


def test_paypal_metadata(integration):
    """Тест метаданных PayPal интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "paypal_create_payout"
    assert metadata.version == "1.0.0"
    assert metadata.name == "PayPal Create Payout"
    assert metadata.category == "payments"
    assert metadata.description == "Создание выплаты (Payout) через PayPal Payouts API"
    assert metadata.icon_s3_key == "icons/integrations/paypal.svg"
    assert metadata.color == "#0070ba"
    assert metadata.credentials_provider == "paypal"
    assert metadata.credentials_strategy == "oauth"
    assert metadata.library_name == "paypal-payouts-sdk>=1.0.0" or metadata.library_name is None
    assert metadata.examples is not None
    assert len(metadata.examples) == 3


@pytest.mark.asyncio
async def test_paypal_execute_success_single_payout(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения PayPal интеграции для одиночной выплаты."""
    # Мокируем ответ PayPal API
    mock_response = MagicMock()
    mock_response.result = {
        "batch_header": {
            "payout_batch_id": "TEST-BATCH-001",
            "batch_status": "PENDING",
            "sender_batch_header": {
                "sender_batch_id": "batch_001",
                "email_subject": "Вам поступил платеж!"
            }
        },
        "items": [
            {
                "payout_item_id": "ITEM-001",
                "transaction_status": "PENDING",
                "payout_item_fee": {"value": "0.25", "currency": "USD"}
            }
        ]
    }
    
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        # Настраиваем mock клиента
        mock_client = MagicMock()
        mock_client.execute = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env
        
        # Мокируем PayoutsPostRequest
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_001",
                "email_subject": "Вам поступил платеж!",
                "currency": "USD",
                "items": [
                    {
                        "receiver": "[email protected]",
                        "amount": 10.00,
                        "note": "Спасибо за вашу работу!",
                        "recipient_type": "EMAIL"
                    }
                ]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert "result" in result["response"]
        
        # Проверяем, что клиент был создан
        mock_client_class.assert_called_once()
        mock_env_class.assert_called_once_with(
            client_id="test-client-id-12345",
            client_secret="test-client-secret-67890"
        )
        mock_request_class.assert_called_once()
        mock_request.request_body.assert_called_once()
        mock_client.execute.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_paypal_execute_success_multiple_payouts(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения PayPal интеграции для множественных выплат."""
    # Мокируем ответ PayPal API
    mock_response = MagicMock()
    mock_response.result = {
        "batch_header": {
            "payout_batch_id": "TEST-BATCH-002",
            "batch_status": "PENDING",
            "sender_batch_header": {
                "sender_batch_id": "batch_002",
                "email_subject": "Выплата за услуги"
            }
        },
        "items": [
            {
                "payout_item_id": "ITEM-001",
                "transaction_status": "PENDING"
            },
            {
                "payout_item_id": "ITEM-002",
                "transaction_status": "PENDING"
            }
        ]
    }
    
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        mock_client = MagicMock()
        mock_client.execute = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_002",
                "email_subject": "Выплата за услуги",
                "currency": "USD",
                "items": [
                    {
                        "receiver": "[email protected]",
                        "amount": 50.00,
                        "note": "Оплата за услуги",
                        "recipient_type": "EMAIL"
                    },
                    {
                        "receiver": "[email protected]",
                        "amount": 75.50,
                        "note": "Оплата за услуги",
                        "recipient_type": "EMAIL"
                    }
                ]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert "result" in result["response"]
        mock_client.execute.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_paypal_execute_success_live_environment(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения PayPal интеграции в live окружении."""
    mock_response = MagicMock()
    mock_response.result = {
        "batch_header": {
            "payout_batch_id": "LIVE-BATCH-001",
            "batch_status": "PENDING"
        }
    }
    
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.LiveEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        mock_client = MagicMock()
        mock_client.execute = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        # Выполняем интеграцию с live окружением
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_live_001",
                "email_subject": "Выплата",
                "currency": "USD",
                "environment": "live",
                "items": [
                    {
                        "receiver": "[email protected]",
                        "amount": 100.00,
                        "recipient_type": "EMAIL"
                    }
                ]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем, что использовалось LiveEnvironment
        mock_env_class.assert_called_once_with(
            client_id="test-client-id-12345",
            client_secret="test-client-secret-67890"
        )
        assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_paypal_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "email_subject": "Test",
            "currency": "USD",
            "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_missing_client_id(integration, logger, bot_id):
    """Тест выполнения с отсутствующим client_id."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "client_secret": "test-secret"
            # client_id отсутствует
        }
    })
    
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "email_subject": "Test",
            "currency": "USD",
            "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "client_id" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_missing_sender_batch_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим sender_batch_id."""
    result = await integration.execute(
        config={
            "email_subject": "Test",
            "currency": "USD",
            "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            # sender_batch_id отсутствует
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "sender_batch_id" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_missing_email_subject(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим email_subject."""
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "currency": "USD",
            "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            # email_subject отсутствует
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "email_subject" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_missing_currency(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим currency."""
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "email_subject": "Test",
            "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            # currency отсутствует
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "currency" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_empty_items(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с пустым массивом items."""
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "email_subject": "Test",
            "currency": "USD",
            "items": []  # пустой массив
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "items" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_items_too_many(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с более чем 5000 items."""
    # Создаем массив из 5001 элемента
    items = [
        {"receiver": f"[email protected]", "amount": 1.00, "recipient_type": "EMAIL"}
        for i in range(5001)
    ]
    
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "email_subject": "Test",
            "currency": "USD",
            "items": items
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "5000" in result["response"]["description"] or "items" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_item_missing_receiver(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующим receiver в item."""
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "email_subject": "Test",
            "currency": "USD",
            "items": [
                {
                    "amount": 10.00,
                    "recipient_type": "EMAIL"
                    # receiver отсутствует
                }
            ]
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "receiver" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_item_invalid_amount(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с невалидной суммой в item."""
    result = await integration.execute(
        config={
            "sender_batch_id": "batch_001",
            "email_subject": "Test",
            "currency": "USD",
            "items": [
                {
                    "receiver": "[email protected]",
                    "amount": -10.00,  # отрицательная сумма
                    "recipient_type": "EMAIL"
                }
            ]
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "amount" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_paypal_id_recipient(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с получателем типа PAYPAL_ID."""
    mock_response = MagicMock()
    mock_response.result = {
        "batch_header": {
            "payout_batch_id": "TEST-BATCH-003",
            "batch_status": "PENDING"
        }
    }
    
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        mock_client = MagicMock()
        mock_client.execute = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_003",
                "email_subject": "Выплата",
                "currency": "EUR",
                "items": [
                    {
                        "receiver": "V7H7Q2Z5QXQHA",
                        "amount": 25.00,
                        "note": "Выплата",
                        "recipient_type": "PAYPAL_ID"
                    }
                ]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        mock_client.execute.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_paypal_execute_http_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки HttpError от PayPal API."""
    # Создаем mock HttpError
    mock_http_error = Exception("PayPal API Error: Invalid credentials")
    mock_http_error.status_code = 401
    
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class, \
         patch('app.integrations.paypal.create_payout.HttpError', Exception):
        
        mock_client = MagicMock()
        mock_client.execute = Mock(side_effect=mock_http_error)
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_001",
                "email_subject": "Test",
                "currency": "USD",
                "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] in [401, 500]
        assert "error" in result["response"]["description"].lower() or "paypal" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_value_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ValueError."""
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        mock_client = MagicMock()
        mock_client.execute = Mock(side_effect=ValueError("Invalid parameter"))
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_001",
                "email_subject": "Test",
                "currency": "USD",
                "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "invalid" in result["response"]["description"].lower() or "parameter" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_unexpected_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки неожиданной ошибки."""
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        mock_client = MagicMock()
        mock_client.execute = Mock(side_effect=RuntimeError("Unexpected error"))
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_001",
                "email_subject": "Test",
                "currency": "USD",
                "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "error" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_library_not_available(integration, logger, bot_id):
    """Тест выполнения когда библиотека не установлена."""
    with patch('app.integrations.paypal.create_payout.PAYPAL_SDK_AVAILABLE', False):
        # Пересоздаем интеграцию, чтобы флаг применился
        integration = PayPalCreatePayoutIntegration()
        
        credentials_resolver = MagicMock(spec=CredentialsResolver)
        credentials_resolver.get_default_for = AsyncMock(return_value={
            "payload": {
                "client_id": "test-id",
                "client_secret": "test-secret"
            }
        })
        
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_001",
                "email_subject": "Test",
                "currency": "USD",
                "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "not installed" in result["response"]["description"].lower() or "not available" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_paypal_execute_credentials_no_payload(integration, credentials_resolver_no_payload, logger, bot_id):
    """Тест выполнения с credentials без payload (обратная совместимость)."""
    mock_response = MagicMock()
    mock_response.result = {
        "batch_header": {
            "payout_batch_id": "TEST-BATCH-004",
            "batch_status": "PENDING"
        }
    }
    
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        mock_client = MagicMock()
        mock_client.execute = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_004",
                "email_subject": "Test",
                "currency": "USD",
                "items": [{"receiver": "[email protected]", "amount": 10.00, "recipient_type": "EMAIL"}]
            },
            credentials_resolver=credentials_resolver_no_payload,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем, что credentials были найдены даже без payload
        mock_env_class.assert_called_once_with(
            client_id="test-client-id-12345",
            client_secret="test-client-secret-67890"
        )
        assert result["response"]["ok"] is True


@pytest.mark.asyncio
async def test_paypal_execute_with_sender_item_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с явно указанным sender_item_id."""
    mock_response = MagicMock()
    mock_response.result = {
        "batch_header": {
            "payout_batch_id": "TEST-BATCH-005",
            "batch_status": "PENDING"
        }
    }
    
    with patch('app.integrations.paypal.create_payout.PayPalHttpClient') as mock_client_class, \
         patch('app.integrations.paypal.create_payout.SandboxEnvironment') as mock_env_class, \
         patch('app.integrations.paypal.create_payout.PayoutsPostRequest') as mock_request_class:
        
        mock_client = MagicMock()
        mock_client.execute = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        mock_env_class.return_value = MagicMock()
        
        mock_request = MagicMock()
        mock_request.request_body = Mock(return_value=None)
        mock_request_class.return_value = mock_request
        
        result = await integration.execute(
            config={
                "sender_batch_id": "batch_005",
                "email_subject": "Test",
                "currency": "USD",
                "items": [
                    {
                        "receiver": "[email protected]",
                        "amount": 10.00,
                        "recipient_type": "EMAIL",
                        "sender_item_id": "custom-item-id-001"
                    }
                ]
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        mock_client.execute.assert_called_once_with(mock_request)

