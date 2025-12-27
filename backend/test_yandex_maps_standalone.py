"""Standalone tests for Yandex Maps Route integration."""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
import httpx

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import the integration class directly
from app.integrations.yandex.maps_route import YandexMapsRouteIntegration


@pytest.fixture
def integration():
    """Create an instance of Yandex Maps Route integration."""
    return YandexMapsRouteIntegration()


@pytest.fixture
def credentials_resolver():
    """Create a mock credentials resolver."""
    resolver = MagicMock()
    resolver.get_default_for = AsyncMock(return_value={
        "api_key": "test-yandex-api-key-123"
    })
    return resolver


@pytest.fixture
def logger():
    """Create a mock logger."""
    logger_mock = MagicMock()
    logger_mock.error = AsyncMock()
    logger_mock.info = AsyncMock()
    logger_mock.debug = AsyncMock()
    return logger_mock


@pytest.mark.asyncio
async def test_yandex_maps_route_metadata(integration):
    """Test Yandex Maps Route integration metadata."""
    metadata = integration.metadata
    # Check required metadata fields
    assert hasattr(metadata, 'name')
    assert hasattr(metadata, 'description')
    assert hasattr(metadata, 'config_schema')
    # Check if the metadata has the expected structure
    assert metadata.id == 'yandex_maps_route'
    assert isinstance(metadata.version, str)
    assert isinstance(metadata.examples, list)


@pytest.mark.asyncio
async def test_yandex_maps_route_execute(integration, credentials_resolver, logger):
    """Test Yandex Maps Route execute method with mocked HTTP response."""
    # Prepare test config according to the schema
    test_config = {
        "origin_lat": 55.75396,
        "origin_lon": 37.620393,
        "destination_lat": 55.74449,
        "destination_lon": 37.718475,
        "mode": "driving",
        "avoid_tolls": False,
        "traffic": "default"
    }
    
    # Mock the HTTP response
    mock_response = {
        "routes": [{
            "distance": {"value": 1000},  # meters
            "duration": {"value": 300},   # seconds
            "legs": [{
                "steps": []
            }]
        }]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        # Configure the mock to return a response with a JSON body
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_get.return_value = mock_response_obj
        
        # Execute the integration
        result = await integration.execute(
            bot_id=UUID("12345678-1234-5678-1234-567812345678"),
            credentials_resolver=credentials_resolver,
            config=test_config,
            logger=logger
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "response" in result
        assert "result" in result["response"]
        assert "data" in result["response"]["result"]
        assert "routes" in result["response"]["result"]["data"]
        assert len(result["response"]["result"]["data"]["routes"]) > 0
        route = result["response"]["result"]["data"]["routes"][0]
        assert "distance" in route
        assert "duration" in route


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short", __file__])
