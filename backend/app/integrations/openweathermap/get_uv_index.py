"""OpenWeatherMap Get UV Index интеграция используя httpx для прямых HTTP запросов."""
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


class OpenweathermapGetUvIndexIntegration(BaseIntegration):
    """Интеграция для получения UV Index через OpenWeatherMap API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_uv_index",
            version="1.0.0",
            name="OpenWeatherMap Get UV Index",
            description="Получение текущего UV Index по координатам через OpenWeatherMap API",
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
                        "description": "Географическая широта"
                    },
                    "lon": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Географическая долгота"
                    }
                }
            },
            # ИСПРАВЛЕНО: провайдер "other" вместо "openweathermap"
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "UV Index для Москвы",
                    "config": {"lat": 55.7558, "lon": 37.6173}
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

            if lat is None or lon is None:
                await logger.error("lat and lon are required")
                return {"response": {"ok": False, "error_code": 400, "description": "lat and lon are required"}}

            # Выполняем запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/uvi",
                    params={"lat": lat, "lon": lon, "appid": api_key}
                )

                if response.status_code == 200:
                    data = response.json()
                    return {"response": {"ok": True, "result": data}}
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    await logger.error(f"OpenWeatherMap API error: {error_message}")
                    return {"response": {"ok": False, "error_code": response.status_code, "description": error_message}}

        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {"response": {"ok": False, "error_code": 500, "description": str(e)}}