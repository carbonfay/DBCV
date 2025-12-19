"""OpenWeatherMap Get Air Pollution интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Используем httpx для прямых HTTP запросов (рекомендуется в SAFE_LIBRARIES.md)
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
            description="Получение данных о текущем и прогнозируемом загрязнении воздуха через OpenWeatherMap Air Pollution API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#f1603d",
            config_schema={
                "type": "object",
                "required": ["location"],
                "properties": {
                    "location": {
                        "type": "string",
                        "title": "Location",
                        "description": "Координаты 'lat,lon' (например: '55.7558,37.6173') или название города для получения координат"
                    },
                    "start": {
                        "type": "integer",
                        "title": "Start",
                        "description": "Unix timestamp начала периода (опционально, для прогноза)"
                    },
                    "end": {
                        "type": "integer",
                        "title": "End",
                        "description": "Unix timestamp конца периода (опционально, для прогноза). Если указан start, то end обязателен"
                    }
                }
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Текущее загрязнение воздуха в Москве",
                    "config": {
                        "location": "55.7558,37.6173"
                    }
                },
                {
                    "title": "Прогноз загрязнения воздуха",
                    "config": {
                        "location": "55.7558,37.6173",
                        "start": 1609459200,
                        "end": 1609545600
                    }
                },
                {
                    "title": "Загрязнение по названию города",
                    "config": {
                        "location": "Moscow,ru"
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
        Выполняет интеграцию используя httpx для прямых HTTP запросов к OpenWeatherMap Air Pollution API.
        
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
                    "description": "httpx library is not installed"
                }
            }
        
        # Получаем API ключ из credentials
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
                    "description": "OpenWeatherMap API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("apikey") or payload.get("key")
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
        location = config.get("location")
        start = config.get("start")
        end = config.get("end")
        
        if not location:
            await logger.error("location is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "location is required"
                }
            }
        
        # Проверяем, что если указан start, то указан и end
        if start is not None and end is None:
            await logger.error("end is required when start is specified")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "end is required when start is specified"
                }
            }
        
        # Парсим координаты или название города
        lat = None
        lon = None
        
        if "," in location:
            try:
                parts = location.split(",")
                if len(parts) == 2:
                    lat_str = parts[0].strip()
                    lon_str = parts[1].strip()
                    try:
                        lat = float(lat_str)
                        lon = float(lon_str)
                        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                            await logger.error(f"Coordinates out of range: {location}")
                            return {
                                "response": {
                                    "ok": False,
                                    "error_code": 400,
                                    "description": f"Coordinates out of range: {location}"
                                }
                            }
                    except ValueError:
                        # Возможно, это название города с запятой (например, "Moscow,ru")
                        # Попробуем получить координаты через Geocoding API
                        pass
                else:
                    # Больше одной запятой - считаем названием города
                    pass
            except Exception:
                pass
        
        # Если координаты не определены, получаем их через Geocoding API
        if lat is None or lon is None:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    geocode_response = await client.get(
                        "https://api.openweathermap.org/geo/1.0/direct",
                        params={
                            "q": location,
                            "limit": 1,
                            "appid": api_key
                        }
                    )
                    
                    if geocode_response.status_code == 200:
                        geocode_data = geocode_response.json()
                        if geocode_data and len(geocode_data) > 0:
                            lat = geocode_data[0].get("lat")
                            lon = geocode_data[0].get("lon")
                        else:
                            await logger.error(f"City not found: {location}")
                            return {
                                "response": {
                                    "ok": False,
                                    "error_code": 404,
                                    "description": f"City not found: {location}"
                                }
                            }
                    else:
                        await logger.error(f"Geocoding API error: {geocode_response.status_code}")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": geocode_response.status_code,
                                "description": "Failed to get coordinates for city"
                            }
                        }
            except Exception as e:
                await logger.error(f"Geocoding error: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": f"Geocoding error: {str(e)}"
                    }
                }
        
        if lat is None or lon is None:
            await logger.error("Failed to determine coordinates")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Failed to determine coordinates"
                }
            }
        
        # Параметры для Air Pollution API
        params = {
            "lat": str(lat),
            "lon": str(lon),
            "appid": api_key
        }
        
        # Если указаны start и end, добавляем их для получения прогноза
        if start is not None and end is not None:
            params["start"] = str(start)
            params["end"] = str(end)
        
        # Используем базовый endpoint /data/2.5/air_pollution
        endpoint = "https://api.openweathermap.org/data/2.5/air_pollution"
        
        # ИСПОЛЬЗУЕМ HTTPX ДЛЯ ПРЯМЫХ HTTP ЗАПРОСОВ К AIR POLLUTION API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    endpoint,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Возвращаем результат в формате системы
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "coord": data.get("coord", {}),
                                "list": data.get("list", [])
                            }
                        }
                    }
                elif response.status_code == 401:
                    await logger.error("Invalid API key")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 401,
                            "description": "Invalid API key"
                        }
                    }
                elif response.status_code == 400:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", "Bad request")
                    await logger.error(f"Bad request: {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": error_message
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
        except httpx.RequestError as e:
            await logger.error(f"Request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Request error: {str(e)}"
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

