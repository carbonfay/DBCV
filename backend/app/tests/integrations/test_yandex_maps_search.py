"""Tests for Yandex Maps Search integration."""
import sys
from pathlib import Path
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Now import the integration
from app.integrations.yandex.maps_search import YandexMapsSearchIntegration

# Mock the credentials and logger
class MockCredentials:
    def __init__(self, api_key="test-api-key"):
        self.api_key = api_key


@pytest.fixture
def integration():
    """Create an instance of Yandex Maps Search integration."""
    return YandexMapsSearchIntegration()


@pytest.fixture
def credentials_resolver():
    """Create a mock credentials resolver."""
    resolver = MagicMock()
    resolver.get_default_for = AsyncMock(return_value=MockCredentials())
    return resolver


@pytest.fixture
def logger():
    """Create a mock logger."""
    return MagicMock()


@pytest.fixture
def bot_id():
    """Create a test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_yandex_maps_search_metadata(integration):
    """Test Yandex Maps Search integration metadata."""
    metadata = integration.metadata
    
    assert metadata.id == "yandex_maps_search"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Yandex Maps Search"
    assert metadata.category == "maps"
    assert metadata.credentials_provider == "yandex_maps"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_yandex_maps_search_success(integration, credentials_resolver, logger, bot_id):
    """Test successful Yandex Maps Search execution."""
    # Mock response data
    mock_response_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Test Location",
                    "description": "Test Description"
                }
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        # Configure the mock
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Execute the integration
        result = await integration.execute(
            config={
                "query": "кафе",
                "lat": 55.751244,
                "lon": 37.618423,
                "radius": 1000,
                "results": 5
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Check the result
        assert result["response"]["ok"] is True
        assert "features" in result["response"]["result"]
        assert len(result["response"]["result"]["features"]) == 1
        assert result["response"]["result"]["features"][0]["properties"]["name"] == "Test Location"
        
        # Check that the API was called with the correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "search-maps.yandex.ru/v1/" in args[0]
        assert kwargs["params"]["apikey"] == "test-api-key"
        assert kwargs["params"]["text"] == "кафе"
        assert "ll" in kwargs["params"]


@pytest.mark.asyncio
async def test_yandex_maps_search_no_credentials(integration, logger, bot_id):
    """Test execution without credentials."""
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    result = await integration.execute(
        config={"query": "кафе"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert "error" in result["response"]
    assert result["response"]["error_code"] == 401
    logger.error.assert_called_with("Yandex Maps API key is not configured")


@pytest.mark.asyncio
async def test_yandex_maps_search_missing_required(integration, credentials_resolver, logger, bot_id):
    """Test execution with missing required parameters."""
    with pytest.raises(KeyError):
        await integration.execute(
            config={},  # Missing required 'query' parameter
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )


@pytest.mark.asyncio
async def test_yandex_maps_search_api_error(integration, credentials_resolver, logger, bot_id):
    """Test handling of API errors."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Configure the mock to raise an exception
        mock_get.side_effect = Exception("API Error")
        
        result = await integration.execute(
            config={"query": "кафе"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert "error" in result["response"]
        assert "API Error" in result["response"]["error"]
        logger.error.assert_called()


@pytest.mark.asyncio
async def test_yandex_maps_search_http_error(integration, credentials_resolver, logger, bot_id):
    """Test handling of HTTP errors."""
    with patch('httpx.AsyncClient.get') as mock_get:
        # Configure the mock to return an error response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid request"}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await integration.execute(
            config={"query": "кафе"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert "error" in result["response"]
        assert result["response"]["error_code"] == 400
        logger.error.assert_called()
