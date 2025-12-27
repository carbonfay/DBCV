"""
Тесты для интеграции OpenWeatherMap Get Daily Forecast.
"""

import pytest
import httpx
import uuid
from unittest.mock import AsyncMock, Mock, patch
from app.integrations.openweathermap.get_daily_forecast import (
    OpenweathermapGetDailyForecastIntegration
)


class TestOpenweathermapGetDailyForecastIntegration:
    """Тесты для интеграции получения ежедневного прогноза погоды."""

    @pytest.fixture
    def mock_credentials_resolver(self):
        """Фикстура для мока CredentialsResolver."""
        mock_resolver = AsyncMock()
        mock_resolver.get_default_for = AsyncMock()
        return mock_resolver

    @pytest.fixture
    def mock_logger(self):
        """Фикстура для мока BotLogger."""
        mock_logger = AsyncMock()
        mock_logger.error = AsyncMock()
        return mock_logger

    @pytest.fixture
    def bot_id(self):
        """Фикстура для bot_id."""
        return uuid.uuid4()

    @pytest.fixture
    def integration(self):
        """Фикстура для создания экземпляра интеграции."""
        return OpenweathermapGetDailyForecastIntegration()

    @pytest.fixture
    def valid_credentials(self):
        """Фикстура с валидными credentials."""
        return {
            "payload": {"api_key": "test_api_key_123"},
            "provider": "other",
            "strategy": "api_key"
        }

    @pytest.fixture
    def api_success_response(self):
        """Фикстура с успешным ответом от OpenWeatherMap API."""
        return {
            "cod": "200",
            "message": 0,
            "cnt": 7,
            "list": [
                {
                    "dt": 1710000000,
                    "temp": {"day": 15.5, "min": 10.2, "max": 18.7},
                    "weather": [{"id": 800, "main": "Clear", "description": "ясно"}]
                }
            ],
            "city": {
                "id": 524901,
                "name": "Москва",
                "country": "RU",
                "coord": {"lon": 37.6176, "lat": 55.7558},
                "population": 0,
                "timezone": 10800
            }
        }

    @pytest.mark.asyncio
    async def test_metadata_correct(self, integration):
        """Тест проверки корректности метаданных интеграции."""
        metadata = integration.metadata

        assert metadata.id == "openweathermap_get_daily_forecast"
        assert metadata.name == "OpenWeatherMap Get Daily Forecast"
        assert metadata.category == "weather"
        assert metadata.version == "1.0.0"
        assert metadata.credentials_provider == "other"
        assert metadata.credentials_strategy == "api_key"
        assert metadata.library_name == "httpx"

        # Проверка config_schema
        schema = metadata.config_schema
        assert schema["type"] == "object"
        assert "lat" in schema["required"]
        assert "lon" in schema["required"]
        assert "cnt" in schema["properties"]
        assert schema["properties"]["cnt"]["default"] == 7
        assert schema["properties"]["cnt"]["maximum"] == 16
        assert schema["properties"]["units"]["enum"] == ["standard", "metric", "imperial"]

        # Проверка examples
        assert len(metadata.examples) == 1
        assert metadata.examples[0]["title"] == "Ежедневный прогноз для Москвы (5 дней)"

    @pytest.mark.asyncio
    async def test_successful_api_call(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials,
        api_success_response
    ):
        """Тест успешного вызова API."""
        # Настраиваем моки
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        with patch("httpx.AsyncClient") as mock_client_class:
            # Используем Mock для response (код интеграции вызывает response.json() синхронно)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_success_response
            mock_response.headers.get.return_value = "application/json"

            # Для async with нужно AsyncMock с __aenter__ и __aexit__
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Выполняем интеграцию
            config = {"lat": 55.7558, "lon": 37.6176, "cnt": 5, "units": "metric", "lang": "ru"}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем результат
            assert result["response"]["ok"] is True
            assert "result" in result["response"]
            # Проверяем данные в результате
            result_data = result["response"]["result"]
            assert result_data["cnt"] == 7
            assert result_data["city"]["name"] == "Москва"

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

        config = {"lat": 55.7558, "lon": 37.6176}
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 401
        assert "credentials" in result["response"]["description"].lower()

    @pytest.mark.asyncio
    async def test_missing_required_params(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials
    ):
        """Тест отсутствия обязательных параметров."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        # Тест без lat
        config = {"lon": 37.6176}
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
        config = {"lat": 55.7558}
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "lon" in result["response"]["description"].lower()

    @pytest.mark.asyncio
    async def test_api_error_response(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials
    ):
        """Тест обработки ошибки от API."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "cod": 401,
                "message": "Invalid API key"
            }
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 401

    @pytest.mark.asyncio
    async def test_http_error_handling(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials
    ):
        """Тест обработки HTTP ошибок."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "cod": 429,
                "message": "Rate limit exceeded"
            }
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 429

    @pytest.mark.asyncio
    async def test_network_error_handling(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials
    ):
        """Тест обработки сетевых ошибок."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.RequestError("Network error")

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 500

    @pytest.mark.asyncio
    async def test_timeout_error_handling(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials
    ):
        """Тест обработки ошибки таймаута."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")

            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is False
            assert result["response"]["error_code"] == 504

    @pytest.mark.asyncio
    async def test_cnt_parameter_boundaries(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials
    ):
        """Тест граничных значений параметра cnt."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"cod": "200", "cnt": 1, "list": []}
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Тест cnt < 1 (должен стать 1)
            config = {"lat": 55.7558, "lon": 37.6176, "cnt": 0}
            await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем параметры запроса
            call_args = mock_client.get.call_args
            called_params = call_args[1]["params"]
            assert called_params["cnt"] == 1  # Должно быть скорректировано до 1

            # Сброс мока для следующего теста
            mock_client.get.reset_mock()
            mock_response.json.return_value = {"cod": "200", "cnt": 16, "list": []}

            # Тест cnt > 16 (должен стать 16)
            config = {"lat": 55.7558, "lon": 37.6176, "cnt": 20}
            await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            call_args = mock_client.get.call_args
            called_params = call_args[1]["params"]
            assert called_params["cnt"] == 16  # Должно быть ограничено до 16

    @pytest.mark.asyncio
    async def test_default_parameter_values(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials
    ):
        """Тест значений параметров по умолчанию."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"cod": "200", "cnt": 7, "list": []}
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Вызываем с минимальным набором параметров
            config = {"lat": 55.7558, "lon": 37.6176}
            await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем параметры запроса
            call_args = mock_client.get.call_args
            called_params = call_args[1]["params"]

            # Проверяем значения по умолчанию
            assert called_params["cnt"] == 7  # По умолчанию
            assert called_params["units"] == "metric"  # По умолчанию
            assert called_params["lang"] == "en"  # По умолчанию

    @pytest.mark.asyncio
    async def test_httpx_not_available(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id
    ):
        """Тест когда httpx не установлен."""
        with patch("app.integrations.openweathermap.get_daily_forecast.HTTPX_AVAILABLE", False):
            with patch("app.integrations.openweathermap.get_daily_forecast.httpx", None):
                config = {"lat": 55.7558, "lon": 37.6176}
                result = await integration.execute(
                    config=config,
                    credentials_resolver=mock_credentials_resolver,
                    bot_id=bot_id,
                    logger=mock_logger
                )

                assert result["response"]["ok"] is False
                assert result["response"]["error_code"] == 500
                assert "httpx" in result["response"]["description"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])