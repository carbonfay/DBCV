"""Тесты для Wildberries Get Orders интеграции."""
import pytest
import httpx
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.wildberries.get_orders import WildberriesGetOrdersIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def get_orders_integration():
    """Создает экземпляр Wildberries Get Orders интеграции."""
    return WildberriesGetOrdersIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "api_key": "test-api-key-12345"
        }
    })
    resolver.get_single_for = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_wildberries_metadata(get_orders_integration):
    """Тест метаданных Wildberries интеграции."""
    metadata = get_orders_integration.metadata
    
    assert metadata.id == "wildberries_get_orders"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Wildberries Get Orders"
    assert metadata.category == "ecommerce"
    assert metadata.credentials_provider == "wildberries"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx>=0.27.0"
    assert metadata.examples is not None
    assert len(metadata.examples) > 0


@pytest.mark.asyncio
async def test_wildberries_execute_success(get_orders_integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Wildberries интеграции."""
    mock_response_data = {
        "orders": [
            {
                "orderId": 123456,
                "date": "2024-01-15T10:00:00Z",
                "status": 1,
                "totalPrice": 1000.50
            }
        ],
        "total": 1
    }
    
    with patch('app.integrations.wildberries.get_orders.httpx') as mock_httpx:
        # Настраиваем mock
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.text = ""
        
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        # Выполняем интеграцию
        result = await get_orders_integration.execute(
            config={
                "dateFrom": "2024-01-01T00:00:00Z",
                "dateTo": "2024-01-31T23:59:59Z",
                "take": 100
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["orders"][0]["orderId"] == 123456
        
        # Проверяем, что HTTP запрос был выполнен
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "suppliers-api.wildberries.ru" in call_args[0][0]
        assert "Authorization" in call_args[1]["headers"]


@pytest.mark.asyncio
async def test_wildberries_execute_no_credentials(get_orders_integration, logger, bot_id):
    """Тест выполнения без credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    credentials_resolver.get_single_for = AsyncMock(return_value=None)
    
    result = await get_orders_integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_wildberries_execute_missing_api_key(get_orders_integration, logger, bot_id):
    """Тест выполнения с отсутствующим API ключом."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {}
    })
    credentials_resolver.get_single_for = AsyncMock(return_value=None)
    
    result = await get_orders_integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_wildberries_execute_api_error(get_orders_integration, credentials_resolver, logger, bot_id):
    """Тест обработки ошибки API."""
    with patch('app.integrations.wildberries.get_orders.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await get_orders_integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401


@pytest.mark.asyncio
async def test_wildberries_execute_timeout(get_orders_integration, credentials_resolver, logger, bot_id):
    """Тест обработки таймаута."""
    with patch('app.integrations.wildberries.get_orders.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.TimeoutException = httpx.TimeoutException
        
        result = await get_orders_integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 504


@pytest.mark.asyncio
async def test_wildberries_execute_backward_compatibility(get_orders_integration, logger, bot_id):
    """Тест обратной совместимости с токенами в разных форматах."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "statistics_token": "test-statistics-token"
        }
    })
    credentials_resolver.get_single_for = AsyncMock(return_value=None)
    
    mock_response_data = {"orders": []}
    
    with patch('app.integrations.wildberries.get_orders.httpx') as mock_httpx:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.text = ""
        
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        result = await get_orders_integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is True
        # Проверяем, что токен был использован
        call_args = mock_client.get.call_args
        assert "Bearer test-statistics-token" in call_args[1]["headers"]["Authorization"]

