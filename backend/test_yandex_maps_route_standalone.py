"""Standalone tests for Yandex Maps Route integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
import math
import json

# Mock the imports that would normally come from the app
class MockBotLogger:
    async def error(self, *args, **kwargs):
        print(f"[ERROR] {args} {kwargs}" if args or kwargs else "")
    async def info(self, *args, **kwargs):
        print(f"[INFO] {args} {kwargs}" if args or kwargs else "")
    async def debug(self, *args, **kwargs):
        print(f"[DEBUG] {args} {kwargs}" if args or kwargs else "")

class MockCredentialsResolver:
    def __init__(self, has_credentials=True):
        self.has_credentials = has_credentials
        self.calls = []
    
    async def get_default_for(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if not self.has_credentials:
            return None
        return {"api_key": "test-api-key-123"}

# Import the integration after setting up mocks
with patch('app.auth.credentials_resolver.CredentialsResolver', MockCredentialsResolver), \
     patch('app.loggers.bot.BotLogger', MockBotLogger):
    from app.integrations.yandex.maps_route import YandexMapsRouteIntegration

# Test data
TEST_CONFIG = {
    "origin_lat": 55.7558,
    "origin_lon": 37.6173,
    "destination_lat": 55.751244,
    "destination_lon": 37.618423,
    "use_mock": True
}

@pytest.fixture
def integration():
    """Create an instance of Yandex Maps Route integration."""
    return YandexMapsRouteIntegration()

@pytest.fixture
def credentials_resolver():
    """Create a mock credentials resolver."""
    return MockCredentialsResolver(has_credentials=True)

@pytest.fixture
def missing_credentials_resolver():
    """Create a mock credentials resolver that returns no credentials."""
    return MockCredentialsResolver(has_credentials=False)

@pytest.fixture
def logger():
    """Create a mock logger."""
    return MockBotLogger()

@pytest.fixture
def bot_id():
    """Create a test bot ID."""
    return UUID("12345678-1234-5678-1234-567812345678")

def test_metadata(integration):
    """Test integration metadata."""
    metadata = integration.metadata
    
    assert metadata.id == "yandex_maps_route"
    assert metadata.version == "1.0.1"
    assert metadata.name == "Yandex Maps Route"
    assert metadata.category == "maps"
    assert metadata.credentials_provider == "yandex"
    assert metadata.credentials_strategy == "api_key"

@pytest.mark.asyncio
async def test_basic_route(integration, credentials_resolver, logger, bot_id):
    """Test basic route calculation in mock mode."""
    result = await integration.execute(TEST_CONFIG, credentials_resolver, bot_id, logger)
    
    assert result["response"]["ok"] is True
    assert "result" in result["response"]
    assert "summary" in result["response"]["result"]
    assert "request" in result["response"]["result"]
    assert "data" in result["response"]["result"]
    
    data = result["response"]["result"]["data"]
    assert data["mock"] is True
    assert data["status"] == "OK"
    assert data["mode"] == "driving"
    assert "route" in data
    assert "legs" in data["route"]

@pytest.mark.asyncio
async def test_missing_credentials(integration, missing_credentials_resolver, logger, bot_id):
    """Test behavior when credentials are missing."""
    # Test with mock mode disabled
    config = TEST_CONFIG.copy()
    config["use_mock"] = False
    
    result = await integration.execute(config, missing_credentials_resolver, bot_id, logger)
    
    # Print debug information
    print("\nTest Missing Credentials Result (mock disabled):")
    print(json.dumps(result, indent=2))
    
    # In non-mock mode, we should get an error about missing credentials
    assert result.get("response", {}).get("ok") is False
    assert result.get("response", {}).get("error_code") == 401
    
    # Test with mock mode enabled (should work without credentials)
    config["use_mock"] = True
    result = await integration.execute(config, missing_credentials_resolver, bot_id, logger)
    
    print("\nTest Missing Credentials Result (mock enabled):")
    print(json.dumps(result, indent=2))
    
    # In mock mode, it should work even without valid credentials
    assert result.get("response", {}).get("ok") is True

@pytest.mark.asyncio
async def test_different_travel_modes(integration, credentials_resolver, logger, bot_id):
    """Test different travel modes in mock mode."""
    modes = ["driving", "walking", "bicycle", "transit", "truck", "scooter"]
    
    for mode in modes:
        config = TEST_CONFIG.copy()
        config["mode"] = mode
        
        result = await integration.execute(config, credentials_resolver, bot_id, logger)
        
        assert result["response"]["ok"] is True
        assert result["response"]["result"]["data"]["mode"] == mode

if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        test_integration = YandexMapsRouteIntegration()
        test_credentials_resolver = MockCredentialsResolver(has_credentials=True)
        test_missing_credentials_resolver = MockCredentialsResolver(has_credentials=False)
        test_logger = MockBotLogger()
        test_bot_id = UUID("12345678-1234-5678-1234-567812345678")
        
        # Run test cases
        print("Running test_metadata...")
        test_metadata(test_integration)
        
        print("\nRunning test_basic_route...")
        await test_basic_route(test_integration, test_credentials_resolver, test_logger, test_bot_id)
        
        print("\nRunning test_missing_credentials...")
        await test_missing_credentials(test_integration, test_missing_credentials_resolver, test_logger, test_bot_id)
        
        print("\nRunning test_different_travel_modes...")
        await test_different_travel_modes(test_integration, test_credentials_resolver, test_logger, test_bot_id)
        
        print("\nAll tests passed!")
    
    asyncio.run(run_tests())
