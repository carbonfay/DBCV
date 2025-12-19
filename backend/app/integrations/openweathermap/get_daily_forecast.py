"""OpenWeatherMap Get Daily Forecast интеграция используя httpx для прямых HTTP запросов."""
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


class OpenweathermapGetDailyForecastIntegration(BaseIntegration):
    """Интеграция для получения ежедневного прогноза погоды через OpenWeatherMap Daily Forecast API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_daily_forecast",
            version="1.0.0",
            name="OpenWeatherMap Get Daily Forecast",
            description="Получение ежедневного прогноза погоды на 7 дней через OpenWeatherMap Daily Forecast API",
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
                        "description": "Название города (например: 'Moscow' или 'Moscow,ru') или координаты 'lat,lon'"
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "enum": ["metric", "imperial", "kelvin"],
                        "default": "metric",
                        "description": "Единицы измерения температуры (metric - Цельсий, imperial - Фаренгейт, kelvin - Кельвин)"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "default": "ru",
                        "description": "Язык ответа (ru, en, и т.д.)"
                    },
                    "cnt": {
                        "type": "integer",
                        "title": "Count",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 7,
                        "description": "Количество дней прогноза (максимум 7, по умолчанию 7)"
                    }
                }
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Ежедневный прогноз для Москвы",
                    "config": {
                        "location": "55.7558,37.6173",
                        "units": "metric",
                        "lang": "ru"
                    }
                },
                {
                    "title": "Ежедневный прогноз на английском",
                    "config": {
                        "location": "51.5074,-0.1278",
                        "units": "imperial",
                        "lang": "en"
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
        units = config.get("units", "metric")
        lang = config.get("lang", "ru")
        cnt = config.get("cnt", 7)
        
        if not location:
            await logger.error("location is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "location is required"
                }
            }
        
        # Определяем, это координаты или название города
        params = {
            "appid": api_key,
            "units": units,
            "lang": lang,
            "cnt": min(max(1, cnt), 7)  # Ограничиваем от 1 до 7
        }
        
        # Проверяем, это координаты (lat,lon) или название города
        if "," in location:
            try:
                parts = location.split(",")
                if len(parts) == 2:
                    lat_str = parts[0].strip()
                    lon_str = parts[1].strip()
                    try:
                        lat = float(lat_str)
                        lon = float(lon_str)
                        # Проверяем диапазоны координат
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            params["lat"] = lat_str
                            params["lon"] = lon_str
                        else:
                            # Выход за диапазон - считаем названием города
                            params["q"] = location
                    except ValueError:
                        # Не числа - считаем названием города
                        params["q"] = location
                else:
                    # Больше одной запятой - считаем названием города
                    params["q"] = location
            except Exception:
                # Ошибка парсинга - считаем названием города
                params["q"] = location
        else:
            # Нет запятой - это название города
            params["q"] = location
        
        # ИСПОЛЬЗУЕМ HTTPX ДЛЯ ПРЯМЫХ HTTP ЗАПРОСОВ К DAILY FORECAST API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/forecast/daily",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Возвращаем результат в формате системы
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "city": {
                                    "id": data.get("city", {}).get("id"),
                                    "name": data.get("city", {}).get("name"),
                                    "country": data.get("city", {}).get("country"),
                                    "coord": data.get("city", {}).get("coord", {}),
                                    "population": data.get("city", {}).get("population"),
                                    "timezone": data.get("city", {}).get("timezone")
                                },
                                "cnt": data.get("cnt"),
                                "cod": data.get("cod"),
                                "message": data.get("message", 0),
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
                elif response.status_code == 404:
                    await logger.error(f"City not found: {location}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"City not found: {location}"
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

