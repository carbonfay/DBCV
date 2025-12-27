"""OpenWeatherMap Get Weather History интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any
from uuid import UUID
import time

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class OpenweathermapGetWeatherHistoryIntegration(BaseIntegration):
    """Интеграция для получения исторических данных о погоде через OpenWeatherMap Time Machine API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_history",
            version="1.0.0",
            name="OpenWeatherMap Get Weather History",
            description="Получение исторических данных о погоде для указанной даты через OpenWeatherMap Time Machine API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#f1603d",
            config_schema={
                "type": "object",
                "required": ["lat", "lon", "dt"],
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
                    "dt": {
                        "type": "integer",
                        "title": "Date/Time",
                        "description": "Дата в формате Unix timestamp (секунды)",
                        "minimum": 0
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "enum": ["standard", "metric", "imperial"],
                        "default": "metric",
                        "description": "Единицы измерения"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "default": "en",
                        "description": "Язык ответа"
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
                    "title": "Исторические данные для Москвы (вчера)",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6176,
                        "dt": int(time.time() - 86400),
                        "units": "metric",
                        "lang": "ru"
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
            dt = config.get("dt")
            units = config.get("units", "metric")
            lang = config.get("lang", "en")

            if lat is None or lon is None:
                await logger.error("lat and lon are required")
                return {"response": {"ok": False, "error_code": 400, "description": "lat and lon are required parameters"}}

            if dt is None:
                await logger.error("dt (timestamp) is required")
                return {"response": {"ok": False, "error_code": 400, "description": "dt (timestamp) is required parameter"}}

            # Формируем параметры запроса
            params = {
                "lat": lat,
                "lon": lon,
                "dt": dt,
                "appid": api_key,
                "units": units,
                "lang": lang
            }

            # Выполняем запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get("https://api.openweathermap.org/data/2.5/onecall/timemachine", params=params)

                if response.status_code == 200:
                    data = response.json()
                    return {"response": {"ok": True, "result": data}}
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    await logger.error(f"OpenWeatherMap API error: {error_message}")
                    return {"response": {"ok": False, "error_code": response.status_code, "description": error_message}}

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP {e.response.status_code}: {str(e)}"
            await logger.error(f"OpenWeatherMap API HTTP error: {error_message}")
            return {"response": {"ok": False, "error_code": e.response.status_code, "description": str(e)}}
        
        except httpx.RequestError as e:
            await logger.error(f"Network error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": f"Network error: {str(e)}"}}
            
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}