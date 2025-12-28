"""Тесты для YooKassa Get Refund интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.yookassa.get_refund import YooKassaGetRefundIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр YooKassa интеграции."""
    return YooKassaGetRefundIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "shop_id": "123456",
            "secret_key": "test_secret_key_12345"
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


def test_yookassa_metadata(integration):
    """Тест метаданных YooKassa интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "yookassa_get_refund"
    assert metadata.version == "1.0.0"
    assert metadata.name == "YooKassa Get Refund"
    assert metadata.category == "payments"
    assert metadata.credentials_provider == "yookassa"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "yookassa>=2.3.0" or metadata.library_name is None


@pytest.mark.asyncio
async def test_yookassa_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения YooKassa интеграции."""
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration') as mock_config:
        
        # Настраиваем mock объекта Refund
        mock_refund = MagicMock()
        mock_refund.to_dict = MagicMock(return_value={
            "id": "2d5b0e00-000f-5000-8000-1a6612345678",
            "status": "succeeded",
            "amount": {
                "value": "20.00",
                "currency": "RUB"
            },
            "payment_id": "2c5b0e00-000f-5000-8000-1a6612345678",
            "created_at": "2025-01-18T10:00:00.000Z",
            "description": "Test refund"
        })
        
        mock_refund_class.find_one = MagicMock(return_value=mock_refund)
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={
                "refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True "2c5b0e00-000f-5000-8000-1a6612345678"
        assert result["response"]["result"]["status"] == "succeeded"
        assert result["response"]["result"]["amount"]["value"] == "20.00"
        assert result["response"]["result"]["amount"]["currency"] == "RUB"
        assert result["response"]["result"]["payment_id"] == "2c5b0e00-000f-5000-8000-1a6612345678"
        
        # Проверяем, что Configuration был настроен
        assert mock_config.account_id == "123456"
        assert mock_config.secret_key == "test_secret_key_12345"
        
        # Проверяем, что метод библиотеки был вызван
        mock_refund_class.find_one.assert_called_once_with("2c5b0e00-000f-5000-8000-1a6612345678")


@pytest.mark.asyncio
async def test_yookassa_execute_success_with_additional_fields(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения с дополнительными полями."""
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration'):
        
        mock_refund = MagicMock()
        mock_refund.to_dict = MagicMock(return_value={
            "id": "2d5b0e00-000f-5000-8000-1a6612345678",
            "status": "succeeded",
            "amount": {
                "value": "20.00",
                "currency": "RUB"
            },
            "payment_id": "2c5b0e00-000f-5000-8000-1a6612345678",
            "created_at": "2025-01-18T10:00:00.000Z",
            "description": "Test refund",
            "receipt_registration": "pending",
            "cancellation_details": {
                "party": "yookassa",
                "reason": "fraud_suspected"
            }
        })
        
        mock_refund_class.find_one = MagicMock(return_value=mock_refund)
        
        result = await integration.execute(
            config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["receipt_registration"] == "pending"
        assert result["response"]["result"]["cancellation_details"]["party"] == "yookassa"
        assert result["response"]["result"]["cancellation_details"]["reason"] == "fraud_suspected"


@pytest.mark.asyncio
async def test_yookassa_execute_no_credentials(integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yookassa_execute_missing_credentials_keys(integration, logger, bot_id):
    """Тест выполнения с неполными credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "shop_id": "123456"
            # Отсутствует secret_key
        }
    })
    
    result = await integration.execute(
        config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "shop_id and secret_key are required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_yookassa_execute_missing_config(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения с отсутствующими параметрами."""
    result = await integration.execute(
        config={},  # Отсутствует refund_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "refund_id is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_yookassa_execute_not_found_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки NotFoundError."""
    from yookassa.domain.exceptions import NotFoundError
    
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration'):
        
        mock_refund_class.find_one = MagicMock(side_effect=NotFoundError("Refund not found"))
        
        result = await integration.execute(
            config={"refund_id": "invalid-refund-id"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "not found" in result["response"]["description"].lower()
        
        # Проверяем, что ошибка была залогирована
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_yookassa_execute_unauthorized_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки UnauthorizedError."""
    from yookassa.domain.exceptions import UnauthorizedError
    
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration'):
        
        mock_refund_class.find_one = MagicMock(side_effect=UnauthorizedError("Invalid credentials"))
        
        result = await integration.execute(
            config={"refund_id": "2d5b0e00-000f-5000-8000-1a6612345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "unauthorized" in result["response"]["description"].lower()
        
        # Проверяем, что ошибка была залогирована
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_yookassa_execute_api_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки ApiError."""
    from yookassa.domain.exceptions import ApiError
    
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration'):
        
        api_error = ApiError("API error occurred")
        api_error.code = 500
        mock_refund_class.find_one = MagicMock(side_effect=api_error)
        
        result = await integration.execute(
            config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "api error" in result["response"]["description"].lower()
        
        # Проверяем, что ошибка была залогирована
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_yookassa_execute_unexpected_error(integration, credentials_resolver, logger, bot_id):
    """Тест обработки неожиданной ошибки."""
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration'):
        
        mock_refund_class.find_one = MagicMock(side_effect=ValueError("Unexpected error"))
        
        result = await integration.execute(
            config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "unexpected error" in result["response"]["description"].lower()
        
        # Проверяем, что ошибка была залогирована
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_yookassa_execute_library_not_available(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения когда библиотека недоступна."""
    # Патчим флаг доступности библиотеки
    with patch('app.integrations.yookassa.get_refund.YOOKASSA_AVAILABLE', False):
        result = await integration.execute(
            config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "library is not installed" in result["response"]["description"].lower()


@pytest.mark.asyncio
async def test_yookassa_execute_credentials_without_payload(integration, logger, bot_id):
    """Тест выполнения с credentials без payload (обратная совместимость)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "shop_id": "123456",
        "secret_key": "test_secret_key_12345"
        # Нет ключа "payload"
    })
    
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration'):
        
        mock_refund = MagicMock()
        mock_refund.to_dict = MagicMock(return_value={
            "id": "2c5b0e00-000f-5000-8000-1a6612345678",
            "status": "succeeded",
            "amount": {"value": "20.00", "currency": "RUB"},
            "payment_id": "2c5b0e00-000f-5000-8000-1a6612345678",
            "created_at": "2025-01-18T10:00:00.000Z",
            "description": "Test refund"
        })
        
        mock_refund_class.find_one = MagicMock(return_value=mock_refund)
        
        result = await integration.execute(
            config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Должно работать с credentials в корне
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == "2c5b0e00-000f-5000-8000-1a6612345678"


@pytest.mark.asyncio
async def test_yookassa_execute_alternative_credential_keys(integration, logger, bot_id):
    """Тест выполнения с альтернативными ключами credentials (account_id вместо shop_id)."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "account_id": "123456",  # Альтернативный ключ для shop_id
            "api_key": "test_api_key_12345"  # Альтернативный ключ для secret_key
        }
    })
    
    with patch('app.integrations.yookassa.get_refund.Refund') as mock_refund_class, \
         patch('app.integrations.yookassa.get_refund.Configuration') as mock_config:
        
        mock_refund = MagicMock()
        mock_refund.to_dict = MagicMock(return_value={
            "id": "30d9cc52-000f-5000-b000-100fcbda564f",
            "status": "succeeded",
            "amount": {"value": "20.00", "currency": "RUB"},
            "payment_id": "2c5b0e00-000f-5000-8000-1a6612345678",
            "created_at": "2025-01-18T10:00:00.000Z",
            "description": "Test refund"
        })
        
        mock_refund_class.find_one = MagicMock(return_value=mock_refund)
        
        result = await integration.execute(
            config={"refund_id": "2c5b0e00-000f-5000-8000-1a6612345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Должно работать с альтернативными ключами
        assert result["response"]["ok"] is True
        assert mock_config.account_id == "123456"
        assert mock_config.secret_key == "test_api_key_12345"










