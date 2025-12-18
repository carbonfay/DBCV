"""OpenWeatherMap UV Index integration using httpx async client."""
from typing import Any, Dict
from uuid import UUID

import httpx

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.loggers.bot import BotLogger


class OpenweathermapGetUvIndexIntegration(BaseIntegration):
    """
    Получение текущего UV Index по координатам через OpenWeatherMap API.

    Пример использования:
        integration = OpenweathermapGetUvIndexIntegration()
        result = await integration.execute(
            config={"lat": 55.7558, "lon": 37.6173},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )
    """

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_uv_index",
            version="1.0.0",
            name="OpenWeatherMap Get UV Index",
            description="Получение текущего UV Index по координатам",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#4DA3FF",
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Географическая широта",
                    },
                    "lon": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Географическая долгота",
                    },
                },
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "UV Index для Москвы",
                    "config": {"lat": 55.7558, "lon": 37.6173},
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """
        Выполняет запрос к OpenWeatherMap для получения UV Index.

        Args:
            config: Параметры интеграции (lat, lon).
            credentials_resolver: Резолвер для получения credentials.
            bot_id: ID бота, для которого запрашиваются credentials.
            logger: Логгер для записи событий.
        """
        # Извлекаем координаты
        lat = config.get("lat")
        lon = config.get("lon")
        if lat is None or lon is None:
            await logger.error("lat and lon are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "lat and lon are required",
                }
            }

        # Получаем credentials для OpenWeatherMap
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="openweathermap",
            strategy="api_key",
        )

        if not creds:
            await logger.error("OpenWeatherMap credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "OpenWeatherMap credentials not found",
                }
            }

        payload = creds.get("payload", {}) or creds
        api_key = payload.get("api_key")
        if not api_key:
            await logger.error(
                f"api_key not found in credentials. Available keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials",
                }
            }

        url = "https://api.openweathermap.org/data/2.5/uvi"
        params = {"lat": lat, "lon": lon, "appid": api_key}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_text = e.response.text
            await logger.error(
                f"OpenWeatherMap HTTP error: {status_code} {error_text}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": status_code,
                    "description": error_text,
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"OpenWeatherMap request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected OpenWeatherMap error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }

        return {"response": {"ok": True, "result": data}}
