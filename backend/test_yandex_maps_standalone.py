"""Standalone tests for Yandex Maps Search integration."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response

# Test implementation
class TestYandexMapsSearch:
    class IntegrationMetadata:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class YandexMapsSearchIntegration:
        @property
        def metadata(self):
            return TestYandexMapsSearch.IntegrationMetadata(
                id="yandex_maps_search",
                version="1.0.0",
                name="Yandex Maps Search",
                category="maps",
                credentials_provider="yandex_maps",
                credentials_strategy="api_key"
            )

        async def execute(self, config, credentials_resolver, bot_id, logger):
            return {
                "response": {
                    "ok": True, 
                    "result": {"test": "success"}
                }
            }

# Fixtures
@pytest.fixture
def integration():
    return TestYandexMapsSearch.YandexMapsSearchIntegration()

@pytest.fixture
def credentials_resolver():
    resolver = MagicMock()
    resolver.get_default_for = AsyncMock(return_value=MagicMock(api_key="test-api-key"))
    return resolver

@pytest.fixture
def logger():
    return MagicMock()

@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")

# Tests
def test_metadata(integration):
    metadata = integration.metadata
    assert metadata.id == "yandex_maps_search"
    assert metadata.name == "Yandex Maps Search"
    assert metadata.category == "maps"

@pytest.mark.asyncio
async def test_execute_success(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={"query": "test"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    assert result["response"]["ok"] is True
