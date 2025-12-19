"""OpenWeatherMap Get UV Index интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class OpenWeatherMapGetUVIndexIntegration(BaseIntegration):
    """Интеграция для получения индекса УФ-излучения из OpenWeatherMap API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_uv_index",
            version="1.0.0",
            name="OpenWeatherMap Get UV Index",
            description="Получение индекса УФ-излучения из OpenWeatherMap API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#5B9BD3",
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {
                        "type": "number",
                        "minimum": -90,
                        "maximum": 90,
                        "title": "Latitude",
                        "description": "Широта для получения UV индекса (например, 55.7558 для Москвы)"
                    },
                    "lon": {
                        "type": "number",
                        "minimum": -180,
                        "maximum": 180,
                        "title": "Longitude",
                        "description": "Долгота для получения UV индекса (например, 37.6176 для Москвы)"
                    }
                }
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить UV-индекс для Москвы",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6176
                    }
                },
                {
                    "title": "Получить UV-индекс для Нью-Йорка",
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
        Выполняет интеграцию используя httpx для прямых вызовов OpenWeatherMap API.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not available"
                }
            }

        # Получаем api_key из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="openweathermap",
            strategy="api_key"
        )

        if not creds:
            await logger.error("OpenWeatherMap credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "OpenWeatherMap api_key not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        api_key = payload.get("api_key") or payload.get("key")
        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key not found in credentials"
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
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            await logger.error("Coordinates are out of valid range")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Latitude must be between -90 and 90, longitude must be between -180 and 180"
                }
            }

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # Формируем URL для запроса к OpenWeatherMap UV API
            base_url = "https://api.openweathermap.org/data/2.5/uvi"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key
            }

            # Выполняем GET-запрос
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url, params=params)

            # Проверяем статус ответа
            if response.status_code != 200:
                await logger.error(f"OpenWeatherMap UV API returned status {response.status_code}: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"API returned status {response.status_code}: {response.text}"
                    }
                }

            # Парсим JSON-ответ
            data = response.json()

            # Извлекаем нужные данные об УФ-индексе
            uv_info = {
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "date_iso": data.get("date_iso"),
                "date": data.get("date"),
                "value": data.get("value"),
                "id": data.get("id")  # может быть null в некоторых ответах
            }

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": uv_info
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP request error: {e}"
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

