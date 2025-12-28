from typing import Any, Dict
from uuid import UUID

import httpx

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.loggers.bot import BotLogger

class OpenweathermapGetCurrentIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_current",
            version="1.0.0",
            name="OpenWeatherMap Get Current",
            description="Get current weather for a city using OpenWeatherMap API.",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#4A90E2",
            config_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "default": "metric",
                        "description": "Units of measurement",
                    },
                },
                "required": ["city"],
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Get current weather for London in metric units",
                    "config": {"city": "London", "units": "metric"},
                },
                {
                    "title": "Get current weather for New York in imperial units",
                    "config": {"city": "New York", "units": "imperial"},
                },
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        city = config.get("city")
        units = config.get("units", "metric")

        if not city:
            await logger.error("city is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "city is required",
                }
            }

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
                    "description": "OpenWeatherMap API key not found",
                }
            }

        payload = creds.get("payload") or creds
        api_key = payload.get("api_key") or payload.get("token") or payload.get("key")
        if not api_key:
            await logger.error(f"api_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "OpenWeatherMap API key not found in credentials",
                }
            }

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "units": units, "appid": api_key}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            return {"response": {"ok": True, "result": data}}
        except httpx.HTTPStatusError as e:
            await logger.error(f"OpenWeatherMap HTTP error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": str(e),
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"OpenWeatherMap request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 502,
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"OpenWeatherMap error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
