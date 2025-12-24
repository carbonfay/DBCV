"""Tests for Google Maps Geocode integration."""
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.google.maps_geocode import GoogleMapsGeocodeIntegration
from app.loggers.bot import BotLogger
import app.integrations.google.maps_geocode as maps_geocode


@pytest.fixture
def integration():
    """Create integration instance."""
    return GoogleMapsGeocodeIntegration()


@pytest.fixture
def bot_id():
    """Create test bot id."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def logger():
    """Create mock logger."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def credentials_resolver():
    """Create mock credentials resolver with API key."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"key": "test-key"}})
    return resolver


@pytest.mark.asyncio
async def test_google_maps_geocode_address_success(
    integration, credentials_resolver, logger, bot_id
):
    """Test successful geocoding by address."""
    with patch.object(maps_geocode, "GOOGLE_MAPS_AVAILABLE", True):
        with patch.object(maps_geocode, "Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.geocode.return_value = [{"formatted_address": "Test Address"}]
            mock_client.return_value = mock_instance

            result = await integration.execute(
                config={"address": "Test Address"},
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger,
            )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["results"][0]["formatted_address"] == "Test Address"
    assert result["response"]["result"]["request"]["address"] == "Test Address"
    mock_client.assert_called_once_with(key="test-key")
    mock_instance.geocode.assert_called_once()


@pytest.mark.asyncio
async def test_google_maps_api_error_handling(
    integration, credentials_resolver, logger, bot_id
):
    """Test handling of Google Maps API errors."""
    with patch.object(maps_geocode, "GOOGLE_MAPS_AVAILABLE", True):
        with patch.object(maps_geocode, "Client") as mock_client:
            api_error = maps_geocode.ApiError("REQUEST_DENIED", "Invalid key")
            api_error.status = "REQUEST_DENIED"
            mock_instance = MagicMock()
            mock_instance.geocode.side_effect = api_error
            mock_client.return_value = mock_instance

            result = await integration.execute(
                config={"address": "Test Address"},
                credentials_resolver=credentials_resolver,
                bot_id=bot_id,
                logger=logger,
            )

    assert result["response"]["ok"] is False
    assert result["response"]["error"]["type"] == "authorization_error"
    assert result["response"]["error"]["status"] == "REQUEST_DENIED"


@pytest.mark.asyncio
async def test_google_maps_response_format(
    integration, credentials_resolver, logger, bot_id
):
    """Test response format for validation errors."""
    with patch.object(maps_geocode, "GOOGLE_MAPS_AVAILABLE", True):
        result = await integration.execute(
            config={},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is False
    assert "error" in result["response"]
    assert result["response"]["error"]["type"] == "validation_error"
    assert result["response"]["error"]["message"] == "address is required"
