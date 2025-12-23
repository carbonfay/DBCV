"""OpenWeatherMap Get UV Index интеграция используя httpx для прямых HTTP запросов."""
import httpx
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class OpenWeatherMapGetUvIndexIntegration(BaseIntegration):
    """Интеграция для получения UV индекса из OpenWeatherMap API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_uv_index",
            version="1.0.0",
            name="OpenWeatherMap Get UV Index",
            description="Получение текущего UV индекса по координатам (широта/долгота) через OpenWeatherMap API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#FF6B6B",
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {
                        "type": "number",
                        "minimum": -90,
                        "maximum": 90,
                        "title": "Latitude",
                        "description": "Широта в десятичном формате (например, 55.7558 для Москвы)"
                    },
                    "lon": {
                        "type": "number",
                        "minimum": -180,
                        "maximum": 180,
                        "title": "Longitude",
                        "description": "Долгота в десятичном формате (например, 37.6173 для Москвы)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Получить UV индекс для Москвы",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6173
                    }
                },
                {
                    "title": "Получить UV индекс для Нью-Йорка",
                    "config": {
                        "lat": 40.7128,
                        "lon": -74.0060
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя прямые HTTP запросы к OpenWeatherMap API.

        Args:
            config: Параметры интеграции (lat, lon)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        # Получаем API ключ из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",  # Используем "other" как провайдер для "Другое - другой провайдер"
            strategy="api_key"
        )

        if not creds:
            await logger.error("OpenWeatherMap credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "OpenWeatherMap API key not found in credentials. Please ensure you have saved your API key with provider 'other' and strategy 'api_key'."
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        api_key = payload.get("api_key") or payload.get("token")
        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "OpenWeatherMap API key not found in credentials"
                }
            }

        # Получаем параметры из config
        lat = config.get("lat")
        lon = config.get("lon")

        if lat is None or lon is None:
            await logger.error("lat and lon are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "lat and lon are required"
                }
            }

        # Проверяем, что координаты в допустимом диапазоне
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            await logger.error(f"Invalid coordinate types: lat={lat} (type: {type(lat)}), lon={lon} (type: {type(lon)})")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Invalid coordinate types. Latitude and longitude must be numeric values."
                }
            }

        if not (-90 <= lat <= 90):
            await logger.error(f"Invalid latitude: {lat}. Must be between -90 and 90.")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Invalid latitude. Must be between -90 and 90."
                }
            }

        if not (-180 <= lon <= 180):
            await logger.error(f"Invalid longitude: {lon}. Must be between -180 and 180.")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Invalid longitude. Must be between -180 and 180."
                }
            }

        # Формируем URL для запроса к OpenWeatherMap UV API (используем HTTPS как рекомендовано)
        url = "https://api.openweathermap.org/data/2.5/uvi"
        # Используем форматирование с 6 знаками после запятой для большей точности
        # Убедимся, что координаты - это числа, а не строки
        params = {
            "lat": float(lat),
            "lon": float(lon),
            "appid": api_key
        }

        # Логируем параметры для отладки
        await logger.info(f"Making request to OpenWeatherMap API with params: lat={params['lat']}, lon={params['lon']}, appid=***{api_key[-4:]}")

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ для HTTP запроса
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                error_content = response.text
                await logger.error(f"OpenWeatherMap API returned status {response.status_code} with content: {error_content}")
                # Try to parse error response as JSON to get more details
                try:
                    error_json = response.json()
                    error_message = error_json.get("message", error_content)
                except:
                    error_message = error_content
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"OpenWeatherMap API error: {error_message}"
                    }
                }

            # Парсим JSON ответ
            data = response.json()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "latitude": float(data.get("lat")) if data.get("lat") is not None else None,
                        "longitude": float(data.get("lon")) if data.get("lon") is not None else None,
                        "date": data.get("date_iso"),
                        "uv_index": float(data.get("value")) if data.get("value") is not None else None,
                        "full_response": data  # Возвращаем полный ответ на случай, если понадобятся дополнительные данные
                    }
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP request error: {str(e)}"
                }
            }
        except httpx.TimeoutException as e:
            await logger.error(f"HTTP request timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 408,
                    "description": f"Request timeout: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }