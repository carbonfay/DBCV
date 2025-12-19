#!/usr/bin/env python3
"""Simple test script for OpenWeatherMap integration without pytest dependency."""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_integration():
    """Test the OpenWeatherMap integration."""
    print("=" * 70)
    print("OpenWeatherMap Daily Forecast Integration - Manual Tests")
    print("=" * 70)
    
    try:
        from app.integrations.weather.openweathermap_daily_forecast import (
            OpenWeatherMapDailyForecastIntegration
        )
        from app.integrations.base import BaseIntegration
        print("\n✓ Import successful")
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        return False
    
    # Test 1: Class structure
    print("\n[Test 1] Class Structure")
    print("-" * 70)
    
    integration = OpenWeatherMapDailyForecastIntegration()
    
    if isinstance(integration, BaseIntegration):
        print("✓ Class inherits from BaseIntegration")
    else:
        print("✗ Class does not inherit from BaseIntegration")
        return False
    
    if hasattr(integration, 'metadata'):
        print("✓ Has metadata property")
    else:
        print("✗ Missing metadata property")
        return False
    
    if asyncio.iscoroutinefunction(integration.execute):
        print("✓ execute() is async method")
    else:
        print("✗ execute() is not async")
        return False
    
    # Test 2: Metadata validation
    print("\n[Test 2] Metadata Validation")
    print("-" * 70)
    
    metadata = integration.metadata
    
    tests = [
        ("id", "openweathermap_daily_forecast"),
        ("version", "1.0.0"),
        ("name", "OpenWeatherMap Get Daily Forecast"),
        ("category", "weather"),
        ("credentials_provider", "openweathermap"),
        ("credentials_strategy", "api_key"),
    ]
    
    for attr, expected_value in tests:
        actual_value = getattr(metadata, attr, None)
        if actual_value == expected_value:
            print(f"✓ {attr}: '{expected_value}'")
        else:
            print(f"✗ {attr}: expected '{expected_value}', got '{actual_value}'")
            return False
    
    # Test 3: Config schema
    print("\n[Test 3] Config Schema")
    print("-" * 70)
    
    schema = metadata.config_schema
    
    if schema.get("type") == "object":
        print("✓ Schema type is 'object'")
    else:
        print("✗ Schema type is not 'object'")
        return False
    
    required_fields = schema.get("required", [])
    if "latitude" in required_fields and "longitude" in required_fields:
        print("✓ Required fields: latitude, longitude")
    else:
        print("✗ Missing required fields")
        return False
    
    properties = schema.get("properties", {})
    required_props = ["latitude", "longitude", "units", "lang"]
    for prop in required_props:
        if prop in properties:
            print(f"✓ Has property: {prop}")
        else:
            print(f"✗ Missing property: {prop}")
            return False
    
    # Test 4: Examples
    print("\n[Test 4] Examples")
    print("-" * 70)
    
    if metadata.examples and len(metadata.examples) > 0:
        print(f"✓ Has {len(metadata.examples)} examples")
        for i, example in enumerate(metadata.examples):
            title = example.get("title", "Unknown")
            print(f"  • Example {i+1}: {title}")
    else:
        print("✗ No examples provided")
        return False
    
    # Test 5: Error handling - missing credentials
    print("\n[Test 5] Error Handling - Missing Credentials")
    print("-" * 70)
    
    mock_credentials_resolver = AsyncMock()
    mock_credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    mock_logger = AsyncMock()
    mock_logger.error = AsyncMock()
    
    result = await integration.execute(
        config={"latitude": 55.7558, "longitude": 37.6173},
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger
    )
    
    if (result["response"]["ok"] is False and 
        result["response"]["error_code"] == 401):
        print("✓ Correctly returns 401 error when credentials missing")
        print(f"  Error message: {result['response']['description']}")
    else:
        print("✗ Incorrect error handling for missing credentials")
        return False
    
    # Test 6: Error handling - missing parameters
    print("\n[Test 6] Error Handling - Missing Parameters")
    print("-" * 70)
    
    mock_credentials_resolver = AsyncMock()
    mock_credentials_resolver.get_default_for = AsyncMock(
        return_value={"payload": {"api_key": "test_key"}}
    )
    
    result = await integration.execute(
        config={"longitude": 37.6173},  # Missing latitude
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger
    )
    
    if (result["response"]["ok"] is False and 
        result["response"]["error_code"] == 400):
        print("✓ Correctly returns 400 error when latitude missing")
        print(f"  Error message: {result['response']['description']}")
    else:
        print("✗ Incorrect error handling for missing parameters")
        return False
    
    # Test 7: Error handling - invalid coordinates
    print("\n[Test 7] Error Handling - Invalid Coordinates")
    print("-" * 70)
    
    result = await integration.execute(
        config={"latitude": 91, "longitude": 37.6173},  # Invalid latitude
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger
    )
    
    if (result["response"]["ok"] is False and 
        result["response"]["error_code"] == 400):
        print("✓ Correctly returns 400 error for invalid latitude (>90)")
        print(f"  Error message: {result['response']['description']}")
    else:
        print("✗ Incorrect validation of latitude range")
        return False
    
    # Test 8: Library verification
    print("\n[Test 8] Library Usage Verification")
    print("-" * 70)
    
    import inspect
    source_code = inspect.getsource(integration.execute)
    
    checks = [
        ("httpx.AsyncClient", "Uses httpx.AsyncClient for HTTP requests"),
        ("credentials_resolver.get_default_for", "Gets credentials via resolver"),
        ("except httpx.HTTPError", "Handles httpx HTTP errors"),
        ("error_code", "Sets error codes in response"),
    ]
    
    for check_str, description in checks:
        if check_str in source_code:
            print(f"✓ {description}")
        else:
            print(f"✗ Missing: {description}")
            return False
    
    # Test 9: Response format
    print("\n[Test 9] Response Format Validation")
    print("-" * 70)
    
    # Create a mock successful response
    from unittest.mock import patch
    
    mock_credentials_resolver = AsyncMock()
    mock_credentials_resolver.get_default_for = AsyncMock(
        return_value={"payload": {"api_key": "test_key"}}
    )
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "name": "Moscow",
        "sys": {"country": "RU", "sunrise": 1639071600, "sunset": 1639101300},
        "coord": {"lat": 55.7558, "lon": 37.6173},
        "timezone": 10800,
        "main": {
            "temp": -5.2,
            "feels_like": -12.5,
            "temp_min": -8.1,
            "temp_max": -2.3,
            "pressure": 1013,
            "humidity": 75
        },
        "visibility": 10000,
        "wind": {"speed": 5.5, "deg": 230},
        "clouds": {"all": 90},
        "weather": [{"main": "Clouds", "description": "overcast clouds", "icon": "04d"}],
        "dt": 1639086600
    }
    
    with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_async_client
        
        result = await integration.execute(
            config={
                "latitude": 55.7558,
                "longitude": 37.6173,
                "units": "metric",
                "lang": "ru"
            },
            credentials_resolver=mock_credentials_resolver,
            bot_id=uuid4(),
            logger=mock_logger
        )
    
    # Check response structure
    if "response" in result:
        print("✓ Response has 'response' key")
    else:
        print("✗ Response missing 'response' key")
        return False
    
    response = result["response"]
    if "ok" in response and response["ok"] is True:
        print("✓ Response has 'ok' field set to True")
    else:
        print("✗ Response 'ok' field is not True")
        return False
    
    if "result" in response:
        print("✓ Response has 'result' field")
        result_data = response["result"]
        
        # Check result structure
        required_keys = ["location", "current_weather", "units", "timestamp", "sunrise", "sunset"]
        for key in required_keys:
            if key in result_data:
                print(f"  ✓ Result has '{key}' field")
            else:
                print(f"  ✗ Result missing '{key}' field")
                return False
        
        # Check location structure
        location = result_data["location"]
        location_keys = ["name", "country", "latitude", "longitude"]
        for key in location_keys:
            if key in location:
                print(f"    ✓ Location has '{key}'")
            else:
                print(f"    ✗ Location missing '{key}'")
                return False
        
        # Check weather structure
        weather = result_data["current_weather"]
        weather_keys = ["temperature", "humidity", "wind_speed", "description", "main"]
        for key in weather_keys:
            if key in weather:
                print(f"    ✓ Weather has '{key}'")
            else:
                print(f"    ✗ Weather missing '{key}'")
                return False
    else:
        print("✗ Response missing 'result' field")
        return False
    
    print("\n" + "=" * 70)
    print("✓ All tests passed successfully!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_integration())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
