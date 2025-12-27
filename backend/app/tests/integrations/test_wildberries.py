"""Тесты для Wildberries интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.wildberries.get_product_info import WildberriesGetProductInfoIntegration
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр Wildberries интеграции."""
    return WildberriesGetProductInfoIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    return resolver


@pytest.fixture
def logger():
    """Создает mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Создает test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_wildberries_metadata(integration):
    """Тест метаданных Wildberries интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "wildberries_get_product_info"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Wildberries Get Product Info"
    assert metadata.category == "ecommerce"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "none"


@pytest.mark.asyncio
async def test_wildberries_execute_success(integration, credentials_resolver, logger, bot_id):
    """Тест успешного выполнения Wildberries интеграции."""
    mock_response_data = {
        "data": {
            "products": [
                {
                    "id": 12345678,
                    "name": "Test Product",
                    "brand": "Test Brand",
                    "priceU": 500000,  # 5000 рублей
                    "salePriceU": 400000,  # 4000 рублей
                    "rating": 4.5,
                    "feedbacks": 100,
                    "supplierId": 12345,
                    "subjName": "Test Category",
                    "subjRootName": "Test Root Category",
                    "sizes": [
                        {
                            "name": "42",
                            "origName": "42 RU",
                            "rank": 1,
                            "optionId": 123,
                            "stocks": [{"wh": 1, "qty": 10}]
                        }
                    ],
                    "colors": [
                        {"name": "Black", "id": 1}
                    ],
                    "pics": ["123/456.jpg"]
                }
            ]
        }
    }
    
    with patch('app.integrations.wildberries.get_product_info.httpx.AsyncClient') as mock_client_class:
        # Настраиваем mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        # Выполняем интеграцию
        result = await integration.execute(
            config={"product_id": "12345678"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["id"] == 12345678
        assert result["response"]["result"]["name"] == "Test Product"
        assert result["response"]["result"]["price"] == 5000
        assert result["response"]["result"]["sale_price"] == 4000
        
        # Проверяем, что HTTP запрос был сделан
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_wildberries_execute_no_product_id(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения без product_id."""
    result = await integration.execute(
        config={},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "Product ID is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_wildberries_execute_product_not_found(integration, credentials_resolver, logger, bot_id):
    """Тест выполнения когда продукт не найден."""
    mock_response_data = {"data": {"products": []}}
    
    with patch('app.integrations.wildberries.get_product_info.httpx.AsyncClient') as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        result = await integration.execute(
            config={"product_id": "99999999"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404