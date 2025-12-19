"""Comprehensive tests for OpenWeatherMap Get Daily Forecast integration."""
import pytest
import json
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.weather import OpenWeatherMapDailyForecastIntegration
from app.integrations.base import IntegrationMetadata


class TestOpenWeatherMapDailyForecastIntegration:
    """Tests for OpenWeatherMapDailyForecastIntegration."""
    
    @pytest.fixture
    def integration(self):
        """Create integration instance."""
        return OpenWeatherMapDailyForecastIntegration()
    
    @pytest.fixture
    def bot_id(self):
        """Create bot ID."""
        return uuid4()
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        logger = AsyncMock()
        logger.error = AsyncMock()
        logger.info = AsyncMock()
        return logger
    
    @pytest.fixture
    def mock_credentials_resolver(self):
        """Create mock credentials resolver."""
        resolver = AsyncMock()
        return resolver
    
    # ========== METADATA TESTS ==========
    
    def test_metadata_structure(self, integration):
        """Test that metadata is properly defined and inherits from BaseIntegration."""
        metadata = integration.metadata
        
        assert isinstance(metadata, IntegrationMetadata)
        assert metadata.id == "openweathermap_daily_forecast"
        assert metadata.version == "1.0.0"
        assert metadata.name == "OpenWeatherMap Get Daily Forecast"
        assert metadata.category == "weather"
        assert metadata.credentials_provider == "openweathermap"
        assert metadata.credentials_strategy == "api_key"
        assert metadata.library_name == "httpx>=0.27.0"
    
    def test_metadata_config_schema(self, integration):
        """Test config schema structure and required fields."""
        metadata = integration.metadata
        schema = metadata.config_schema
        
        assert schema["type"] == "object"
        assert "latitude" in schema["required"]
        assert "longitude" in schema["required"]
        assert "properties" in schema
        
        props = schema["properties"]
        
        # Check latitude property
        assert props["latitude"]["type"] == "number"
        assert props["latitude"]["title"] == "Latitude"
        
        # Check longitude property
        assert props["longitude"]["type"] == "number"
        assert props["longitude"]["title"] == "Longitude"
        
        # Check units property
        assert props["units"]["type"] == "string"
        assert "enum" in props["units"]
        assert "metric" in props["units"]["enum"]
        assert "imperial" in props["units"]["enum"]
        assert "standard" in props["units"]["enum"]
        assert props["units"]["default"] == "metric"
        
        # Check lang property
        assert props["lang"]["type"] == "string"
        assert props["lang"]["default"] == "en"
    
    def test_metadata_has_examples(self, integration):
        """Test that examples are provided in metadata."""
        metadata = integration.metadata
        
        assert metadata.examples is not None
        assert len(metadata.examples) >= 2
        
        # Check first example
        example1 = metadata.examples[0]
        assert "title" in example1
        assert "config" in example1
        assert example1["config"]["latitude"] == 55.7558
        assert example1["config"]["longitude"] == 37.6173
        assert example1["config"]["units"] == "metric"
        
        # Check second example
        example2 = metadata.examples[1]
        assert "title" in example2
        assert "config" in example2
        assert example2["config"]["latitude"] == 40.7128
        assert example2["config"]["longitude"] == -74.0060
        assert example2["config"]["units"] == "imperial"
    
    # ========== CREDENTIAL TESTS ==========
    
    @pytest.mark.asyncio
    async def test_execute_missing_credentials(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute when credentials are not found."""
        mock_credentials_resolver.get_default_for = AsyncMock(return_value=None)
        
        result = await integration.execute(
            config={"latitude": 55.7558, "longitude": 37.6173},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "api_key" in result["response"]["description"].lower() or "credentials" in result["response"]["description"].lower()
        await mock_logger.error.assert_called()
        
        # Verify correct credentials request
        mock_credentials_resolver.get_default_for.assert_called_once_with(
            bot_id=bot_id,
            provider="openweathermap",
            strategy="api_key"
        )
    
    @pytest.mark.asyncio
    async def test_execute_missing_api_key_in_payload(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with missing api_key in credentials payload."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"other_field": "value"}}
        )
        
        result = await integration.execute(
            config={"latitude": 55.7558, "longitude": 37.6173},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "api_key" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_api_key_backward_compatibility(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test that api_key can be extracted from both payload and root level."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"api_key": "test_key_direct"}
        )
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: self._mock_weather_response()
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={"latitude": 55.7558, "longitude": 37.6173},
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
    
    # ========== PARAMETER VALIDATION TESTS ==========
    
    @pytest.mark.asyncio
    async def test_execute_missing_latitude(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with missing latitude parameter."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        result = await integration.execute(
            config={"longitude": 37.6173},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "latitude" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_missing_longitude(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with missing longitude parameter."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        result = await integration.execute(
            config={"latitude": 55.7558},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "longitude" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_invalid_latitude_too_high(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with latitude > 90."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        result = await integration.execute(
            config={"latitude": 91, "longitude": 37.6173},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "latitude" in result["response"]["description"].lower()
        assert "between -90 and 90" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_invalid_latitude_too_low(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with latitude < -90."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        result = await integration.execute(
            config={"latitude": -91, "longitude": 37.6173},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "latitude" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_invalid_longitude_too_high(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with longitude > 180."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        result = await integration.execute(
            config={"latitude": 55.7558, "longitude": 181},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "longitude" in result["response"]["description"].lower()
        assert "between -180 and 180" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_invalid_longitude_too_low(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with longitude < -180."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        result = await integration.execute(
            config={"latitude": 55.7558, "longitude": -181},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "longitude" in result["response"]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_with_string_coordinates(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with string coordinates (should be converted to float)."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: self._mock_weather_response()
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={
                    "latitude": "55.7558",  # String
                    "longitude": "37.6173",  # String
                },
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
    
    @pytest.mark.asyncio
    async def test_execute_with_invalid_string_coordinates(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with non-numeric string coordinates."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        result = await integration.execute(
            config={"latitude": "not_a_number", "longitude": 37.6173},
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "invalid" in result["response"]["description"].lower()
    
    # ========== UNITS PARAMETER TESTS ==========
    
    @pytest.mark.asyncio
    async def test_execute_with_metric_units(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with metric units."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: self._mock_weather_response()
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={
                    "latitude": 55.7558,
                    "longitude": 37.6173,
                    "units": "metric"
                },
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
        # Verify httpx was called with correct units
        call_args = mock_async_client.get.call_args
        assert call_args[1]["params"]["units"] == "metric"
    
    @pytest.mark.asyncio
    async def test_execute_with_imperial_units(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with imperial units."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: self._mock_weather_response()
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={
                    "latitude": 55.7558,
                    "longitude": 37.6173,
                    "units": "imperial"
                },
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
        call_args = mock_async_client.get.call_args
        assert call_args[1]["params"]["units"] == "imperial"
    
    @pytest.mark.asyncio
    async def test_execute_with_invalid_units(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test execute with invalid units (should default to metric)."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: self._mock_weather_response()
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={
                    "latitude": 55.7558,
                    "longitude": 37.6173,
                    "units": "invalid_unit"
                },
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
        # Should default to metric
        call_args = mock_async_client.get.call_args
        assert call_args[1]["params"]["units"] == "metric"
    
    # ========== SUCCESSFUL EXECUTION TESTS ==========
    
    @pytest.mark.asyncio
    async def test_execute_success_moscow(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test successful execution for Moscow."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: self._mock_weather_response()
        
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
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is True
        assert "result" in result["response"]
        
        result_data = result["response"]["result"]
        
        # Check location
        assert result_data["location"]["name"] == "Moscow"
        assert result_data["location"]["country"] == "RU"
        assert result_data["location"]["latitude"] == 55.7558
        assert result_data["location"]["longitude"] == 37.6173
        
        # Check weather
        weather = result_data["current_weather"]
        assert weather["temperature"] == -5.2
        assert weather["feels_like"] == -12.5
        assert weather["humidity"] == 75
        assert weather["wind_speed"] == 5.5
        assert weather["main"] == "Clouds"
        assert weather["description"] == "overcast clouds"
        
        # Check units
        assert result_data["units"] == "metric"
        
        await mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_response_format(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test that response follows the required format."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: self._mock_weather_response()
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={"latitude": 55.7558, "longitude": 37.6173},
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        # Verify structure
        assert "response" in result
        assert "ok" in result["response"]
        assert "result" in result["response"]
        
        # Verify result structure
        res = result["response"]["result"]
        assert "location" in res
        assert "current_weather" in res
        assert "units" in res
        assert "timestamp" in res
        assert "sunrise" in res
        assert "sunset" in res
    
    # ========== API ERROR TESTS ==========
    
    @pytest.mark.asyncio
    async def test_execute_api_error_401_unauthorized(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test handling of API 401 Unauthorized error."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "invalid_key"}}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"cod":"401", "message":"Invalid API key. Please see http://openweathermap.org/faq#error401 for more info."}'
        mock_response.json = lambda: {
            "cod": "401",
            "message": "Invalid API key. Please see http://openweathermap.org/faq#error401 for more info."
        }
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={"latitude": 55.7558, "longitude": 37.6173},
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "Invalid API key" in result["response"]["description"]
    
    @pytest.mark.asyncio
    async def test_execute_api_error_404_not_found(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test handling of API 404 Not Found error."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"cod":"404", "message":"city not found"}'
        mock_response.json = lambda: {"cod": "404", "message": "city not found"}
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={"latitude": 55.7558, "longitude": 37.6173},
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 404
    
    @pytest.mark.asyncio
    async def test_execute_http_error(
        self,
        integration,
        bot_id,
        mock_logger,
        mock_credentials_resolver
    ):
        """Test handling of HTTP errors from httpx."""
        mock_credentials_resolver.get_default_for = AsyncMock(
            return_value={"payload": {"api_key": "test_key"}}
        )
        
        with patch("app.integrations.weather.openweathermap_daily_forecast.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.get = AsyncMock(
                side_effect=Exception("Connection timeout")
            )
            mock_client.return_value = mock_async_client
            
            result = await integration.execute(
                config={"latitude": 55.7558, "longitude": 37.6173},
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "Connection timeout" in result["response"]["description"]
    
    # ========== HELPER METHODS ==========
    
    def _mock_weather_response(self):
        """Helper method to generate mock weather API response."""
        return {
            "name": "Moscow",
            "sys": {
                "country": "RU",
                "sunrise": 1639071600,
                "sunset": 1639101300
            },
            "coord": {
                "lat": 55.7558,
                "lon": 37.6173
            },
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
            "wind": {
                "speed": 5.5,
                "deg": 230
            },
            "clouds": {
                "all": 90
            },
            "weather": [
                {
                    "main": "Clouds",
                    "description": "overcast clouds",
                    "icon": "04d"
                }
            ],
            "dt": 1639086600
        }
