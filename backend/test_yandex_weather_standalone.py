#!/usr/bin/env python
"""Standalone test runner for YandexWeatherGetForecastIntegration.

This script runs basic tests without requiring full backend dependencies
or conftest.py. It can be used for quick validation of the integration.
"""
import asyncio
import sys
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch


async def test_metadata():
    """Test metadata is correctly set."""
    from app.integrations.yandex_weather_get_forecast.get_forecast import (
        YandexWeatherGetForecastIntegration,
    )

    integration = YandexWeatherGetForecastIntegration()
    metadata = integration.metadata

    assert metadata.id == "yandex_weather_get_forecast", f"Expected id 'yandex_weather_get_forecast', got {metadata.id}"
    assert metadata.version == "1.0.0", f"Expected version '1.0.0', got {metadata.version}"
    assert metadata.category == "weather", f"Expected category 'weather', got {metadata.category}"
    assert metadata.credentials_provider == "yandex_weather"
    assert metadata.credentials_strategy == "api_key"
    assert "latitude" in metadata.config_schema["properties"]
    print("✓ test_metadata passed")


async def test_execute_success():
    """Test successful API response."""
    from app.integrations.yandex_weather_get_forecast.get_forecast import (
        YandexWeatherGetForecastIntegration,
    )

    integration = YandexWeatherGetForecastIntegration()

    # Create mocks
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "now": 1600000000,
        "now_dt": "2020-09-13T12:00:00Z",
        "forecasts": [{"date": "2020-09-13", "parts": []}],
        "info": {"lat": 55.75, "lon": 37.62, "url": "https://weather.yandex.ru/"},
    }

    async_mock_client = MagicMock()
    async_mock_client.get = AsyncMock(return_value=mock_response)

    credentials_resolver = MagicMock()
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"api_key": "test-key"}})

    logger = MagicMock()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")

    # Patch AsyncClient
    with patch("app.integrations.yandex_weather_get_forecast.get_forecast.httpx.AsyncClient") as mock_client_class:
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.__aenter__.return_value = async_mock_client
        mock_client_instance.__aenter__ = AsyncMock(return_value=async_mock_client)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        result = await integration.execute(
            config={"latitude": 55.75, "longitude": 37.62},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True, f"Expected ok=True, got {result}"
    assert "result" in result["response"]
    assert result["response"]["result"]["info"]["lat"] == 55.75
    print("✓ test_execute_success passed")


async def test_execute_no_credentials():
    """Test error when credentials are missing."""
    from app.integrations.yandex_weather_get_forecast.get_forecast import (
        YandexWeatherGetForecastIntegration,
    )

    integration = YandexWeatherGetForecastIntegration()

    credentials_resolver = MagicMock()
    credentials_resolver.get_default_for = AsyncMock(return_value=None)

    logger = MagicMock()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")

    result = await integration.execute(
        config={"latitude": 55.75, "longitude": 37.62},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401, f"Expected error_code 401, got {result['response']['error_code']}"
    print("✓ test_execute_no_credentials passed")


async def test_execute_invalid_coordinates():
    """Test error with invalid latitude."""
    from app.integrations.yandex_weather_get_forecast.get_forecast import (
        YandexWeatherGetForecastIntegration,
    )

    integration = YandexWeatherGetForecastIntegration()

    credentials_resolver = MagicMock()
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"api_key": "test-key"}})

    logger = MagicMock()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")

    result = await integration.execute(
        config={"latitude": 100.0, "longitude": 37.62},  # Invalid: > 90
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400, f"Expected error_code 400, got {result['response']['error_code']}"
    print("✓ test_execute_invalid_coordinates passed")


async def main():
    """Run all tests."""
    print("Running YandexWeatherGetForecastIntegration tests...\n")
    try:
        await test_metadata()
        await test_execute_success()
        await test_execute_no_credentials()
        await test_execute_invalid_coordinates()
        print("\n✅ All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
