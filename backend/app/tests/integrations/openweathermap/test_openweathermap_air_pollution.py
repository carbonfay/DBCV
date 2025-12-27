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
            "provider": "other",
            "strategy": "api_key"
        }

    @pytest.fixture
    def valid_credentials_object(self):
        """Фикстура с валидными credentials в формате объекта."""
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
        assert metadata.credentials_provider == "other"
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
        assert len(metadata.examples) == 1
        assert metadata.examples[0]["title"] == "Текущее загрязнение воздуха в Москве"

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
            # Создаем мок ответа - НЕ AsyncMock для json()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_success_response_current
            mock_response.headers.get.return_value = "application/json"
            mock_response.raise_for_status = Mock()  # Просто Mock, не AsyncMock

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Выполняем интеграцию
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
            # Проверяем структуру ответа
            result_data = result["response"]["result"]
            assert "list" in result_data
            assert len(result_data["list"]) == 1
            assert result_data["list"][0]["main"]["aqi"] == 2

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
        # Настраиваем моки
        mock_credentials_resolver.get_default_for.return_value = valid_credentials_object

        with patch("httpx.AsyncClient") as mock_client_class:
            # Создаем мок ответа - НЕ AsyncMock для json()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_success_response_history
            mock_response.headers.get.return_value = "application/json"
            mock_response.raise_for_status = Mock()

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get.return_value = mock_response

            mock_client_class.return_value = mock_client

            # Выполняем интеграцию
            config = {"lat": 55.7558, "lon": 37.6176, "start": 1672531200, "end": 1672617600}
            result = await integration.execute(
                config=config,
                credentials_resolver=mock_credentials_resolver,
                bot_id=bot_id,
                logger=mock_logger
            )

            # Проверяем результат
            assert result["response"]["ok"] is True
            result_data = result["response"]["result"]
            assert len(result_data["list"]) == 2

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
            # Создаем мок ответа с ошибкой
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.headers.get.return_value = "application/json"
            mock_response.json.return_value = {"message": "Invalid API key"}
            
            # ВАЖНО: raise_for_status должен выбрасывать исключение
            mock_response.raise_for_status = Mock(
                side_effect=httpx.HTTPStatusError(
                    "401 Unauthorized",
                    request=Mock(),
                    response=mock_response
                )
            )

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
            # Создаем мок ответа с ошибкой 429
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers.get.return_value = "application/json"
            mock_response.json.return_value = {"message": "Rate limit exceeded"}
            
            mock_response.raise_for_status = Mock(
                side_effect=httpx.HTTPStatusError(
                    "429 Too Many Requests",
                    request=Mock(),
                    response=mock_response
                )
            )

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
            mock_response = Mock()
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
            assert result["response"]["error_code"] == 500  # В коде интеграции всегда 500 для таймаутов

    @pytest.mark.asyncio
    async def test_httpx_not_available(
        self,
        integration,
        mock_credentials_resolver,
        mock_logger,
        bot_id
    ):
        """Тест когда httpx не установлен."""
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
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"coord": {}, "list": []}
            mock_response.headers.get.return_value = "application/json"
            mock_response.raise_for_status = Mock()
            
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])