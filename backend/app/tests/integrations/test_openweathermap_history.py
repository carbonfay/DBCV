"""
Тесты для интеграции OpenWeatherMap Get Weather History.
"""

import pytest
import httpx
import uuid
import time
from unittest.mock import AsyncMock, Mock, patch
from app.integrations.openweathermap.get_history import (
    OpenweathermapGetWeatherHistoryIntegration
)


class TestOpenweathermapGetWeatherHistoryIntegration:
    """Тесты для интеграции получения исторических данных о погоде."""

    @pytest.fixture
    def mock_credentials_resolver(self):
        """Фикстура для мока CredentialsResolver."""
        mock_resolver = AsyncMock()
        return mock_resolver

    @pytest.fixture
    def mock_logger(self):
        """Фикстура для мока BotLogger."""
        mock_logger = AsyncMock()
        return mock_logger

    @pytest.fixture
    def bot_id(self):
        """Фикстура для bot_id."""
        return uuid.uuid4()

    @pytest.fixture
    def integration(self):
        """Фикстура для создания экземпляра интеграции."""
        return OpenweathermapGetWeatherHistoryIntegration()

    @pytest.fixture
    def valid_credentials_dict(self):
        """Фикстура с валидными credentials в формате словаря."""
        return {
            "payload": {"api_key": "test_api_key_789"},
            "provider": "openweathermap",
            "strategy": "api_key"
        }

    @pytest.fixture
    def api_success_response(self):
        """Фикстура с успешным ответом от OpenWeatherMap Time Machine API."""
        return {
            "lat": 55.7558,
            "lon": 37.6176,
            "timezone": "Europe/Moscow",
            "timezone_offset": 10800,
            "current": {
                "dt": 1672531200,
                "temp": -5.5,
                "feels_like": -8.2,
                "pressure": 1013,
                "humidity": 85,
                "dew_point": -7.1,
                "uvi": 0.5,
                "clouds": 75,
                "visibility": 10000,
                "wind_speed": 3.1,
                "wind_deg": 180,
                "weather": [
                    {
                        "id": 601,
                        "main": "Snow",
                        "description": "snow",
                        "icon": "13d"
                    }
                ]
            },
            "hourly": [
                {
                    "dt": 1672527600,
                    "temp": -5.2,
                    "feels_like": -7.9,
                    "pressure": 1013,
                    "humidity": 84
                },
                {
                    "dt": 1672531200,
                    "temp": -5.5,
                    "feels_like": -8.2,
                    "pressure": 1013,
                    "humidity": 85
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_metadata_correct(self, integration):
        """Тест проверки корректности метаданных интеграции."""
        metadata = integration.metadata

        assert metadata.id == "openweathermap_get_history"
        assert metadata.name == "OpenWeatherMap Get Weather History"
        assert metadata.category == "weather"
        assert metadata.version == "1.0.0"
        assert metadata.credentials_provider == "openweathermap"
        assert metadata.credentials_strategy == "api_key"
        assert metadata.library_name == "httpx"

        # Проверка config_schema
        schema = metadata.config_schema
        assert schema["type"] == "object"
        assert "lat" in schema["required"]
        assert "lon" in schema["required"]
        assert "dt" in schema["required"]
        assert "units" in schema["properties"]
        assert "lang" in schema["properties"]
        assert schema["properties"]["units"]["default"] == "metric"
        assert schema["properties"]["lang"]["default"] == "en"
        assert schema["additionalProperties"] is False

        # Проверка examples
        assert len(metadata.examples) == 3
        assert metadata.examples[0]["title"] == "Исторические данные для Москвы (вчера)"
        assert metadata.examples[1]["title"] == "Исторические данные для Лондона (неделю назад)"
        assert metadata.examples[2]["title"] == "Новый Год в Нью-Йорке (2023)"

    @pytest.mark.asyncio
    async def test_successful_api_call(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict,
        api_success_response
    ):
        """Тест успешного вызова API для исторических данных."""
        # Настраиваем моки
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_success_response
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Выполняем интеграцию (исторические данные)
            config = {
                "lat": 55.7558,
                "lon": 37.6176,
                "dt": 1672531200,  # 1 января 2023
                "units": "metric",
                "lang": "ru"
            }
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем результат
            assert result["response"]["ok"] is True
            assert "result" in result["response"]
            assert result["response"]["result"]["lat"] == 55.7558
            assert result["response"]["result"]["lon"] == 37.6176
            assert result["response"]["result"]["count"] == 2
            assert len(result["response"]["result"]["hourly"]) == 2
            assert "current" in result["response"]["result"]

            # Проверяем параметры запроса
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "https://api.openweathermap.org/data/2.5/onecall/timemachine" in str(call_args[0])
            
            called_params = call_args[1]["params"]
            assert called_params["lat"] == 55.7558
            assert called_params["lon"] == 37.6176
            assert called_params["dt"] == 1672531200
            assert called_params["units"] == "metric"
            assert called_params["lang"] == "ru"
            assert called_params["appid"] == "test_api_key_789"

    @pytest.mark.asyncio
    async def test_missing_credentials(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id
    ):
        """Тест отсутствия credentials."""
        mock_credentials_resolver.get_default_for.return_value = None

        config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "credentials" in result["response"]["description"].lower()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_required_params(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест отсутствия обязательных параметров."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        # Тест без lat
        config = {"lon": 37.6176, "dt": 1672531200}
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "lat" in result["response"]["description"].lower()

        # Тест без lon
        config = {"lat": 55.7558, "dt": 1672531200}
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "lon" in result["response"]["description"].lower()

        # Тест без dt
        config = {"lat": 55.7558, "lon": 37.6176}
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "dt" in result["response"]["description"].lower()

    @pytest.mark.asyncio
    async def test_timestamp_in_future_warning(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест предупреждения при timestamp в будущем."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"lat": 55.7558, "lon": 37.6176, "current": {}, "hourly": []}
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            
            mock_client_class.return_value = mock_client

            # Текущее время + 1 день (будущее)
            future_dt = int(time.time()) + 86400
            config = {"lat": 55.7558, "lon": 37.6176, "dt": future_dt}
            
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Должно сработать предупреждение, но не ошибка
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "not in the past" in warning_msg

    @pytest.mark.asyncio
    async def test_api_error_401_invalid_key(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки ошибки 401 (неверный API ключ)."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 401
            assert "invalid" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once_with("Invalid API key")

    @pytest.mark.asyncio
    async def test_api_error_400_invalid_timestamp(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки ошибки 400 с неверным timestamp."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Invalid dt parameter"}
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 9999999999}  # Неверный timestamp
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 400
            assert "timestamp" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error_400_invalid_coordinates(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки ошибки 400 с неверными координатами."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Wrong coordinates"}
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            config = {"lat": 999, "lon": 999, "dt": 1672531200}  # Неверные координаты
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 400
            assert "coordinates" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error_429_rate_limit(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки ошибки 429 (Rate Limit)."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 429
            assert "rate limit" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once_with("Rate limit exceeded")

    @pytest.mark.asyncio
    async def test_http_error_handling(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки HTTP ошибок через httpx.HTTPStatusError."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            # Создаём HTTP ошибку 404
            mock_response = AsyncMock()
            mock_response.status_code = 404
            error = httpx.HTTPStatusError(
                "Not Found",
                request=Mock(),
                response=mock_response
            )
            mock_client.get.side_effect = error
            
            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 404
            assert "http error" in result["response"]["description"].lower()

    @pytest.mark.asyncio
    async def test_network_error_handling(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки сетевых ошибок."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.RequestError("Network error")

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500
            assert "request error" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_error_handling(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки ошибки таймаута."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 504
            assert "timeout" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_httpx_not_available(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id
    ):
        """Тест когда httpx не установлен."""
        # Мокаем глобальную переменную HTTPX_AVAILABLE
        with patch("app.integrations.openweathermap.get_history.HTTPX_AVAILABLE", False):
            with patch("app.integrations.openweathermap.get_history.httpx", None):
                config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
                result = await integration.execute(
                    config=config,
                    credentials_resolver=mock_credentials_resolver,
                    bot_id=bot_id,
                    logger=mock_logger
                )

                assert result["response"]["ok"] is False
                assert result["response"]["error_code"] == 500
                assert "httpx" in result["response"]["description"].lower()
                mock_logger.error.assert_called_once_with("httpx library is not available")

    @pytest.mark.asyncio
    async def test_default_parameter_values(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест значений параметров по умолчанию."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"lat": 55.7558, "lon": 37.6176, "current": {}, "hourly": []}
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            
            mock_client_class.return_value = mock_client

            # Вызываем без units и lang (должны примениться значения по умолчанию)
            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем параметры запроса
            called_params = mock_client.get.call_args[1]["params"]
            assert called_params["units"] == "metric"  # По умолчанию из metadata
            assert called_params["lang"] == "en"       # По умолчанию из metadata

    @pytest.mark.asyncio
    async def test_credentials_various_formats(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id
    ):
        """Тест обработки различных форматов credentials."""
        # Тест 1: Словарь с api_key в корне
        creds_format1 = {"api_key": "test_key_direct"}
        mock_credentials_resolver.get_default_for.return_value = creds_format1

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"lat": 55.7558, "lon": 37.6176, "current": {}, "hourly": []}
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            
            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is True
            # Проверяем, что api_key передался в запрос
            called_params = mock_client.get.call_args[1]["params"]
            assert called_params["appid"] == "test_key_direct"

    @pytest.mark.asyncio
    async def test_unexpected_error_handling(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки неожиданных ошибок."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            # Симулируем неожиданную ошибку
            mock_client.get.side_effect = ValueError("Unexpected error in parsing")

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176, "dt": 1672531200}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500
            assert "unexpected" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])