"""Тесты для Wildberries Get Order интеграции."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.integrations.wildberries.get_order import WildberriesGetOrderIntegration
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр интеграции для тестирования."""
    return WildberriesGetOrderIntegration()


@pytest.fixture
def mock_credentials_resolver():
    """Создает mock CredentialsResolver."""
    resolver = AsyncMock()
    return resolver


@pytest.fixture
def mock_logger():
    """Создает mock BotLogger."""
    logger = AsyncMock(spec=BotLogger)
    return logger


@pytest.fixture
def bot_id():
    """Возвращает тестовый bot_id."""
    return UUID("12345678-1234-5678-1234-567812345678")


class TestWildberriesGetOrderIntegration:
    """Тесты для WildberriesGetOrderIntegration."""
    
    def test_metadata(self, integration):
        """Проверяет метаданные интеграции."""
        metadata = integration.metadata
        
        assert metadata.id == "wildberries_get_order"
        assert metadata.version == "1.0.0"
        assert metadata.name == "Wildberries Get Order"
        assert metadata.category == "ecommerce"
        assert metadata.credentials_provider == "wildberries"
        assert metadata.credentials_strategy == "api_key"
        assert "order_id" in metadata.config_schema["required"]
        assert "order_id" in metadata.config_schema["properties"]
        assert "detailed" in metadata.config_schema["properties"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_order_id(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет ошибку при отсутствии order_id."""
        config = {"detailed": False}
        
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "order_id" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_credentials(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет ошибку при отсутствии credentials."""
        config = {"order_id": "12345678", "detailed": False}
        mock_credentials_resolver.get_default_for.return_value = None
        
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "Wildberries" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_missing_api_token(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет ошибку при отсутствии API token в credentials."""
        config = {"order_id": "12345678", "detailed": False}
        mock_credentials_resolver.get_default_for.return_value = {
            "payload": {"some_field": "value"}
        }
        
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "token" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_successful_request(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет успешный запрос к Wildberries API."""
        config = {"order_id": "12345678", "detailed": False}
        mock_credentials_resolver.get_default_for.return_value = {
            "payload": {"api_token": "test_token"}
        }
        
        mock_response = {
            "orders": [
                {
                    "id": "12345678",
                    "number": "WB001",
                    "date": "2024-01-01T00:00:00Z",
                    "status": "delivered",
                    "total": 1000,
                    "currency_code": "RUB"
                }
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client
            
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_client.get.return_value = mock_response_obj
            
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["order_id"] == "12345678"
        assert result["response"]["result"]["number"] == "WB001"
        assert result["response"]["result"]["status"] == "delivered"
    
    @pytest.mark.asyncio
    async def test_execute_detailed_request(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет детальный запрос к API."""
        config = {"order_id": "12345678", "detailed": True}
        mock_credentials_resolver.get_default_for.return_value = {
            "payload": {"api_token": "test_token"}
        }
        
        mock_response = {
            "orders": [
                {
                    "id": "12345678",
                    "number": "WB001",
                    "date": "2024-01-01T00:00:00Z",
                    "status": "delivered",
                    "status_id": 3,
                    "status_description": "Доставлено",
                    "total": 1000,
                    "convertedPrice": 1000,
                    "currency_code": "RUB",
                    "items": [{"id": 1, "name": "Product"}],
                    "address": "Moscow",
                    "supplier_id": "123",
                    "client_id": "456",
                    "payment_type": "card",
                    "comments": "Test order"
                }
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client
            
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_client.get.return_value = mock_response_obj
            
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
        assert "status_id" in result["response"]["result"]
        assert "status_description" in result["response"]["result"]
        assert "items" in result["response"]["result"]
        assert "address" in result["response"]["result"]
    
    @pytest.mark.asyncio
    async def test_execute_api_error_401(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет обработку ошибки 401 (Unauthorized)."""
        config = {"order_id": "12345678", "detailed": False}
        mock_credentials_resolver.get_default_for.return_value = {
            "payload": {"api_token": "invalid_token"}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client
            
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 401
            mock_client.get.return_value = mock_response_obj
            
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "authentication" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_api_error_404(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет обработку ошибки 404 (Not Found)."""
        config = {"order_id": "nonexistent", "detailed": False}
        mock_credentials_resolver.get_default_for.return_value = {
            "payload": {"api_token": "test_token"}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client
            
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 404
            mock_client.get.return_value = mock_response_obj
            
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
        assert "not found" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_timeout_error(self, integration, mock_credentials_resolver, mock_logger, bot_id):
        """Проверяет обработку timeout ошибки."""
        import httpx
        
        config = {"order_id": "12345678", "detailed": False}
        mock_credentials_resolver.get_default_for.return_value = {
            "payload": {"api_token": "test_token"}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client
            
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 504
        assert "timeout" in result["response"]["description"].lower()
