"""Тесты для интеграции Wildberries Get Product Info."""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.integrations.wildberries.get_product_info import WildberriesGetProductInfoIntegration
from app.auth.credentials_resolver import CredentialsResolver


@pytest.fixture
def integration():
    """Фикстура для интеграции Wildberries Get Product Info."""
    return WildberriesGetProductInfoIntegration()


@pytest.fixture
def mock_credentials_resolver():
    """Фикстура для мокирования CredentialsResolver."""
    resolver = AsyncMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def mock_logger():
    """Фикстура для мокирования BotLogger."""
    logger = AsyncMock()
    logger.error = AsyncMock()
    logger.info = AsyncMock()
    return logger


@pytest.mark.asyncio
async def test_wildberries_get_product_info_metadata(integration):
    """Тест метаданных интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "wildberries_get_product_info"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Wildberries Get Product Info"
    assert metadata.category == "ecommerce"
    assert "nm_id" in metadata.config_schema["properties"]


@pytest.mark.asyncio
async def test_wildberries_get_product_info_missing_nm_id(integration, mock_credentials_resolver, mock_logger):
    """Тест интеграции с отсутствующим nm_id."""
    config = {}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "nm_id is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_wildberries_get_product_info_invalid_nm_id(integration, mock_credentials_resolver, mock_logger):
    """Тест интеграции с невалидным nm_id."""
    config = {"nm_id": "invalid"}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "must be a numeric value" in result["response"]["description"]


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_wildberries_get_product_info_success(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест успешного выполнения интеграции."""
    # Подготовим mock ответ от API
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "product": {
                "id": 123456789,
                "name": "Тестовый товар",
                "brand": "Тестовый бренд",
                "price": 1000,
                "rating": 4.5
            }
        }
    }
    mock_get.return_value = mock_response
    
    config = {"nm_id": "123456789"}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is True
    assert result["response"]["result"]["nm_id"] == 123456789
    assert result["response"]["result"]["name"] == "Тестовый товар"
    assert result["response"]["result"]["brand"] == "Тестовый бренд"


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_wildberries_get_product_info_api_error(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест обработки ошибки API."""
    # Подготовим mock ответ с ошибкой
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Product not found"
    mock_get.return_value = mock_response
    
    config = {"nm_id": "999999999"}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404


@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_wildberries_get_product_info_http_error(mock_get, integration, mock_credentials_resolver, mock_logger):
    """Тест обработки HTTP ошибки."""
    # Симулируем исключение при HTTP запросе
    mock_get.side_effect = Exception("Network error")
    
    config = {"nm_id": "123456789"}
    bot_id = UUID(int=1)
    
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=bot_id,
        logger=mock_logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500