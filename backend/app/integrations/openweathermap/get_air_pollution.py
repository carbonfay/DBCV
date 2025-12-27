"""OpenWeatherMap Get Air Pollution интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class OpenweathermapGetAirPollutionIntegration(BaseIntegration):
    """Интеграция для получения данных о загрязнении воздуха через OpenWeatherMap Air Pollution API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_air_pollution",
            version="1.0.0",
            name="OpenWeatherMap Get Air Pollution",
            description="Получение данных о загрязнении воздуха (AQI) через OpenWeatherMap Air Pollution API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#f1603d",
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Географическая широта (-90 до 90)",
                        "minimum": -90,
                        "maximum": 90
                    },
                    "lon": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Географическая долгота (-180 до 180)",
                        "minimum": -180,
                        "maximum": 180
                    },
                    "start": {
                        "type": "integer",
                        "title": "Start Time",
                        "description": "Начало периода в Unix timestamp (секунды)",
                        "minimum": 0
                    },
                    "end": {
                        "type": "integer",
                        "title": "End Time",
                        "description": "Конец периода в Unix timestamp (секунды)",
                        "minimum": 0
                    }
                },
                "additionalProperties": False
            },
            # ИСПРАВЛЕНО: провайдер "other" вместо "openweathermap"
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Текущее загрязнение воздуха в Москве",
                    "config": {"lat": 55.7558, "lon": 37.6176}
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
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {"response": {"ok": False, "error_code": 500, "description": "httpx library is not installed"}}

        try:
            # Получаем API ключ из credentials (провайдер "other")
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="other",
                strategy="api_key"
            )

            if not creds:
                await logger.error("API credentials not found")
                return {"response": {"ok": False, "error_code": 401, "description": "API key not found in credentials"}}

            # Извлекаем API ключ
            api_key = None
            if isinstance(creds, dict):
                payload = creds.get("payload", creds)
                if isinstance(payload, dict):
                    api_key = payload.get("api_key") or payload.get("apikey") or payload.get("key")
            elif hasattr(creds, 'api_key'):
                api_key = creds.api_key
            elif hasattr(creds, 'apikey'):
                api_key = creds.apikey
            elif hasattr(creds, 'key'):
                api_key = creds.key

            if not api_key:
                await logger.error("API key not found in credentials")
                return {"response": {"ok": False, "error_code": 401, "description": "API key not found in credentials"}}

            # Получаем параметры
            lat = config.get("lat")
            lon = config.get("lon")
            start = config.get("start")
            end = config.get("end")

            if lat is None or lon is None:
                await logger.error("lat and lon are required")
                return {"response": {"ok": False, "error_code": 400, "description": "lat and lon are required parameters"}}

            # Формируем параметры запроса
            params = {"lat": lat, "lon": lon, "appid": api_key}
            if start is not None:
                params["start"] = start
                if end is not None:
                    params["end"] = end
                else:
                    await logger.error("end parameter is required when start is specified")
                    return {"response": {"ok": False, "error_code": 400, "description": "end parameter is required when start is specified"}}

            # Выполняем запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get("https://api.openweathermap.org/data/2.5/air_pollution", params=params)
                response.raise_for_status()  # Это выбросит httpx.HTTPStatusError для статусов 4xx/5xx
                
                if response.status_code == 200:
                    data = response.json()
                    return {"response": {"ok": True, "result": data}}
                    
        except httpx.HTTPStatusError as e:
            # Обработка HTTP ошибок (401, 404, 429 и т.д.)
            error_message = str(e)
            await logger.error(f"OpenWeatherMap API error: {error_message}")
            return {"response": {"ok": False, "error_code": e.response.status_code, "description": error_message}}
            
        except httpx.RequestError as e:
            # Сетевые ошибки
            await logger.error(f"Network error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}
            
        except Exception as e:
            # Все остальные ошибки
            await logger.error(f"Unexpected error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}