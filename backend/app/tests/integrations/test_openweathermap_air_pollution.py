"""
Тесты для интеграции OpenWeatherMap Get Air Pollution.
"""

import pytest
import httpx
import uuid
from unittest.mock import AsyncMock, Mock, patch
from app.integrations.openweathermap.get_air_pollution import (
    OpenweathermapGetAirPollutionIntegration
)


class TestOpenweathermapGetAirPollutionIntegration:
    """Тесты для интеграции получения данных о загрязнении воздуха."""

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
        return OpenweathermapGetAirPollutionIntegration()

    @pytest.fixture
    def valid_credentials_dict(self):
        """Фикстура с валидными credentials в формате словаря."""
        return {
            "payload": {"api_key": "test_api_key_456"},
            "provider": "openweathermap",
            "strategy": "api_key"
        }

    @pytest.fixture
    def valid_credentials_object(self):
        """Фикстура с валидными credentials в формате объекта."""
        from unittest.mock import Mock
        mock_creds = Mock()
        mock_creds.payload = {"api_key": "test_api_key_456"}
        return mock_creds

    @pytest.fixture
    def api_success_response_current(self):
        """Фикстура с успешным ответом для текущих данных."""
        return {
            "coord": {"lon": 37.6176, "lat": 55.7558},
            "list": [
                {
                    "main": {"aqi": 2},
                    "components": {
                        "co": 201.94053649902344,
                        "no": 0.01877197064459324,
                        "no2": 0.7711350917816162,
                        "o3": 68.66455078125,
                        "so2": 0.6407499313354492,
                        "pm2_5": 0.5,
                        "pm10": 0.540438711643219,
                        "nh3": 0.12369127571582794
                    },
                    "dt": 1710000000
                }
            ]
        }

    @pytest.fixture
    def api_success_response_history(self):
        """Фикстура с успешным ответом для исторических данных."""
        return {
            "coord": {"lon": 37.6176, "lat": 55.7558},
            "list": [
                {
                    "main": {"aqi": 3},
                    "components": {"co": 250.5, "no2": 1.2, "pm2_5": 15.0},
                    "dt": 1672531200
                },
                {
                    "main": {"aqi": 2},
                    "components": {"co": 180.3, "no2": 0.8, "pm2_5": 8.5},
                    "dt": 1672617600
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_metadata_correct(self, integration):
        """Тест проверки корректности метаданных интеграции."""
        metadata = integration.metadata

        assert metadata.id == "openweathermap_get_air_pollution"
        assert metadata.name == "OpenWeatherMap Get Air Pollution"
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
        assert "start" in schema["properties"]
        assert "end" in schema["properties"]
        assert schema["additionalProperties"] is False

        # Проверка examples
        assert len(metadata.examples) == 3
        assert metadata.examples[0]["title"] == "Текущее загрязнение воздуха в Москве"
        assert metadata.examples[1]["title"] == "Загрязнение воздуха в Пекине"
        assert metadata.examples[2]["title"] == "Исторические данные загрязнения"

    @pytest.mark.asyncio
    async def test_successful_api_call_current(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict,
        api_success_response_current
    ):
        """Тест успешного вызова API для текущих данных."""
        # Настраиваем моки
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_success_response_current
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Выполняем интеграцию (текущие данные)
            config = {"lat": 55.7558, "lon": 37.6176}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем результат
            assert result["response"]["ok"] is True
            assert "result" in result["response"]
            assert result["response"]["result"]["count"] == 1
            assert result["response"]["result"]["list"][0]["main"]["aqi"] == 2

            # Проверяем параметры запроса
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "https://api.openweathermap.org/data/2.5/air_pollution" in str(call_args[0])
            
            called_params = call_args[1]["params"]
            assert called_params["lat"] == 55.7558
            assert called_params["lon"] == 37.6176
            assert called_params["appid"] == "test_api_key_456"
            assert "start" not in called_params
            assert "end" not in called_params

    @pytest.mark.asyncio
    async def test_successful_api_call_historical(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_object,
        api_success_response_history
    ):
        """Тест успешного вызова API для исторических данных."""
        # Настраиваем моки (используем объект вместо словаря)
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_object

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_success_response_history
            mock_response.headers.get.return_value = "application/json"

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Выполняем интеграцию (исторические данные)
            config = {"lat": 55.7558, "lon": 37.6176, "start": 1672531200, "end": 1672617600}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем результат
            assert result["response"]["ok"] is True
            assert result["response"]["result"]["count"] == 2
            assert len(result["response"]["result"]["list"]) == 2

            # Проверяем параметры запроса
            called_params = mock_client.get.call_args[1]["params"]
            assert called_params["start"] == 1672531200
            assert called_params["end"] == 1672617600

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
        valid_credentials_dict
    ):
        """Тест отсутствия обязательных параметров."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

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
    async def test_start_without_end(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест указания start без end."""
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_dict

        config = {"lat": 55.7558, "lon": 37.6176, "start": 1672531200}
        result = await integration.execute(
            config=config,
            credentials_resolver=mock_credentials_resolver,
            bot_id=bot_id,
            logger=mock_logger
        )

        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 400
        assert "end" in result["response"]["description"].lower()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error_401(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id,
        valid_credentials_dict
    ):
        """Тест обработки ошибки 401 от API."""
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

            config = {"lat": 55.7558, "lon": 37.6176}
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

            config = {"lat": 55.7558, "lon": 37.6176}
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

            config = {"lat": 55.7558, "lon": 37.6176}
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

            config = {"lat": 55.7558, "lon": 37.6176}
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

            config = {"lat": 55.7558, "lon": 37.6176}
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
        with patch("app.integrations.openweathermap.get_air_pollution.HTTPX_AVAILABLE", False):
            with patch("app.integrations.openweathermap.get_air_pollution.httpx", None):
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
        creds_format1 = {"api_key": "test_key_1"}
        mock_credentials_resolver.get_default_for.return_value = creds_format1

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"coord": {}, "list": []}
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            
            mock_client_class.return_value = mock_client

            config = {"lat": 55.7558, "lon": 37.6176}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            assert result["response"]["ok"] is True
            # Проверяем, что api_key передался в запрос
            called_params = mock_client.get.call_args[1]["params"]
            assert called_params["appid"] == "test_key_1"

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
            mock_client.get.side_effect = ValueError("Unexpected error")

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
            assert "unexpected" in result["response"]["description"].lower()
            mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])