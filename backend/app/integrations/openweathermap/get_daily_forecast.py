"""OpenWeatherMap Get Daily Forecast интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any
from uuid import UUID
import time

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Используем httpx для прямых HTTP запросов
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class OpenweathermapGetDailyForecastIntegration(BaseIntegration):
    """Интеграция для получения ежедневного прогноза погоды через OpenWeatherMap Daily Forecast API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_daily_forecast",
            version="1.0.0",
            name="OpenWeatherMap Get Daily Forecast",
            description="Получение ежедневного прогноза погоды на 1-16 дней через OpenWeatherMap Daily Forecast API",
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
                    "cnt": {
                        "type": "integer",
                        "title": "Days Count",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 16,
                        "description": "Количество дней прогноза (максимум 16, по умолчанию 7)"
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "enum": ["standard", "metric", "imperial"],
                        "default": "metric",
                        "description": "Единицы измерения (standard - Кельвин, metric - Цельсий, imperial - Фаренгейт)"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "default": "en",
                        "description": "Язык ответа (en, ru, и т.д.)"
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
                    "title": "Ежедневный прогноз для Москвы (5 дней)",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6176,
                        "cnt": 5,
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
        """
        Выполняет интеграцию используя httpx для прямых HTTP запросов к OpenWeatherMap Daily Forecast API.
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        try:
            # Получаем API ключ из credentials (провайдер "other")
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="other",
                strategy="api_key"
            )

            if not creds:
                await logger.error("API credentials not found for OpenWeatherMap")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "API key not found in credentials"
                    }
                }

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
                await logger.error(f"API key not found in credentials")
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
            cnt = config.get("cnt", 7)
            units = config.get("units", "metric")
            lang = config.get("lang", "en")

            if lat is None or lon is None:
                await logger.error("lat and lon are required")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "lat and lon are required parameters"
                    }
                }

            # Формируем параметры запроса
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "cnt": min(max(1, cnt), 16),
                "units": units,
                "lang": lang
            }

            # Выполняем запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/forecast/daily",
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "response": {
                            "ok": True,
                            "result": data
                        }
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    await logger.error(f"OpenWeatherMap API error: {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": error_message
                        }
                    }

        except httpx.TimeoutException as e:
            await logger.error(f"Request timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": "Request timeout"
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