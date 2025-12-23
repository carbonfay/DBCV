"""
Тесты для интеграции OpenWeatherMap Get Daily Forecast.
"""

import pytest
import httpx
import uuid
from unittest.mock import AsyncMock, Mock, patch, PropertyMock
from app.integrations.openweathermap.get_daily_forecast import (
    OpenweathermapGetDailyForecastIntegration
)


class TestOpenweathermapGetDailyForecastIntegration:
    """Тесты для интеграции получения ежедневного прогноза погоды."""

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
        return OpenweathermapGetDailyForecastIntegration()

    @pytest.fixture
    def valid_credentials(self):
        """Фикстура с валидными credentials."""
        return {
            "payload": {"api_key": "test_api_key_123"},
            "provider": "openweathermap",
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
        assert metadata.credentials_provider == "openweathermap"
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
        assert len(metadata.examples) >= 1
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
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_success_response
            mock_response.headers.get.return_value = "application/json"
            mock_response.raise_for_status.return_value = None

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

            # ОТЛАДКА: выводим результат для анализа
            print(f"Result: {result}")
            
            # Проверяем результат - должен быть True
            # Проблема: в коде интеграции проверка HTTPX_AVAILABLE
            if "ok" in result.get("response", {}):
                assert result["response"]["ok"] is True, f"Expected ok: True, got: {result}"
            else:
                # Возможно, формат ответа другой
                assert False, f"Unexpected result format: {result}"

            if result["response"]["ok"]:
                assert "result" in result["response"]
                assert result["response"]["result"]["cnt"] == 7
                assert result["response"]["result"]["city"]["name"] == "Москва"

            # Проверяем, что запрос был сделан с правильными параметрами
            mock_credentials_resolver.get_default_for.assert_called_once_with(
                bot_id=bot_id,
                provider="openweathermap",
                strategy="api_key"
            )
            mock_client.get.assert_called_once()

            # Проверяем query parameters
            call_args = mock_client.get.call_args
            assert "https://api.openweathermap.org/data/2.5/forecast/daily" in str(call_args[0])

            called_params = call_args[1]["params"]
            assert called_params["lat"] == 55.7558
            assert called_params["lon"] == 37.6176
            assert called_params["cnt"] == 5
            assert called_params["units"] == "metric"
            assert called_params["lang"] == "ru"
            assert called_params["appid"] == "test_api_key_123"

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
        mock_logger.error.assert_called_once()

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
            mock_response = AsyncMock()
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
            # В коде интеграции при 401 возвращается error_code 401
            assert result["response"]["error_code"] == 401
            assert "Invalid API key" in result["response"]["description"]

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
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
    
            # Симулируем HTTP ошибку 429 (Rate Limit)
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_response.headers.get.return_value = "application/json"
            mock_response.json.return_value = {"cod": 429, "message": "Rate limit exceeded"}
            # ИМПОРТАНТНО: нужно создать исключение для raise_for_status
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Rate limited",
                request=Mock(),
                response=mock_response
            )

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
            # В коде интеграции при HTTP ошибках возвращается статус код ошибки
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
            assert "network" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once()

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
            mock_response = AsyncMock()
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
            mock_response = AsyncMock()
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
            assert called_params["cnt"] == 7  # По умолчанию из config_schema
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
        # ВАЖНО: HTTPX_AVAILABLE - это глобальная переменная в модуле, не атрибут класса
        # Нужно мокать её в модуле, а не в объекте
        
        with patch("app.integrations.openweathermap.get_daily_forecast.HTTPX_AVAILABLE", False):
            # Также нужно заменить httpx на None
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
                mock_logger.error.assert_called_once_with("httpx library is not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])