"""OpenWeatherMap Get Daily Forecast интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx (уже есть в requirements.txt)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class OpenWeatherMapDailyForecastIntegration(BaseIntegration):
    """Интеграция для получения прогноза погоды на день через OpenWeatherMap API используя httpx."""
    
    # OpenWeatherMap API endpoint
    API_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_daily_forecast",
            version="1.0.0",
            name="OpenWeatherMap Get Daily Forecast",
            description="Получение прогноза погоды на день через OpenWeatherMap API с использованием httpx",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#FF6B35",
            config_schema={
                "type": "object",
                "required": ["latitude", "longitude"],
                "properties": {
                    "latitude": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Широта местоположения (например, 55.7558 для Москвы)"
                    },
                    "longitude": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Долгота местоположения (например, 37.6173 для Москвы)"
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "enum": ["metric", "imperial", "standard"],
                        "default": "metric",
                        "description": "Единицы измерения: metric (°C, м/с), imperial (°F, миль/ч), standard (K, м/с)"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "default": "en",
                        "description": "Язык описания погоды (en, ru, fr, de, es, ja и т.д.)"
                    }
                }
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Прогноз для Москвы в Celsius",
                    "config": {
                        "latitude": 55.7558,
                        "longitude": 37.6173,
                        "units": "metric",
                        "lang": "ru"
                    }
                },
                {
                    "title": "Прогноз для Нью-Йорка в Fahrenheit",
                    "config": {
                        "latitude": 40.7128,
                        "longitude": -74.0060,
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
        Выполняет интеграцию используя httpx для прямых запросов к OpenWeatherMap API.
        
        Args:
            config: Параметры интеграции с latitude, longitude и опциональными units, lang
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер для записи логов
        
        Returns:
            Результат выполнения в формате системы:
            {"response": {"ok": True, "result": {...}}} или
            {"response": {"ok": False, "error_code": ..., "description": "..."}}
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
        
        # Получаем API key из credentials
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
        
        api_key = payload.get("api_key") or payload.get("key")
        if not api_key:
            await logger.error(f"api_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials"
                }
            }
        
        # Получаем параметры из config
        latitude = config.get("latitude")
        longitude = config.get("longitude")
        units = config.get("units", "metric")
        lang = config.get("lang", "en")
        
        # Валидация обязательных параметров
        if latitude is None or longitude is None:
            await logger.error("latitude and longitude are required parameters")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "latitude and longitude are required"
                }
            }
        
        # Валидация типов параметров и диапазонов
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            
            # Проверяем диапазоны координат
            if not (-90 <= latitude <= 90):
                raise ValueError("latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("longitude must be between -180 and 180")
        except (ValueError, TypeError) as e:
            await logger.error(f"Invalid latitude or longitude: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid latitude or longitude: {str(e)}"
                }
            }
        
        # Валидация units
        if units not in ["metric", "imperial", "standard"]:
            await logger.info(f"Invalid units '{units}', using 'metric' as default")
            units = "metric"
        
        try:
            # ИСПОЛЬЗУЕМ HTTPX НАПРЯМУЮ ДЛЯ ПРЯМЫХ ЗАПРОСОВ К OPENWEATHERMAP API
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.API_BASE_URL,
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": api_key,
                        "units": units,
                        "lang": lang
                    }
                )
                
                # Проверяем статус ответа
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message", "Unknown error from OpenWeatherMap API")
                        error_code = int(error_data.get("cod", 500))
                    except Exception:
                        error_message = f"HTTP {response.status_code}: {response.text}"
                        error_code = response.status_code
                    
                    await logger.error(
                        f"OpenWeatherMap API error: {error_code} - {error_message}"
                    )
                    return {
                        "response": {
                            "ok": False,
                            "error_code": error_code,
                            "description": error_message
                        }
                    }
                
                data = response.json()
                
                # Форматируем результат в удобный вид
                result = {
                    "location": {
                        "name": data.get("name", "Unknown"),
                        "country": data.get("sys", {}).get("country", ""),
                        "latitude": data.get("coord", {}).get("lat"),
                        "longitude": data.get("coord", {}).get("lon"),
                        "timezone": data.get("timezone")
                    },
                    "current_weather": {
                        "temperature": data.get("main", {}).get("temp"),
                        "feels_like": data.get("main", {}).get("feels_like"),
                        "temp_min": data.get("main", {}).get("temp_min"),
                        "temp_max": data.get("main", {}).get("temp_max"),
                        "pressure": data.get("main", {}).get("pressure"),
                        "humidity": data.get("main", {}).get("humidity"),
                        "visibility": data.get("visibility"),
                        "wind_speed": data.get("wind", {}).get("speed"),
                        "wind_degree": data.get("wind", {}).get("deg"),
                        "wind_gust": data.get("wind", {}).get("gust"),
                        "cloudiness": data.get("clouds", {}).get("all"),
                        "description": data.get("weather", [{}])[0].get("description", ""),
                        "main": data.get("weather", [{}])[0].get("main", ""),
                        "icon": data.get("weather", [{}])[0].get("icon", "")
                    },
                    "units": units,
                    "timestamp": data.get("dt"),
                    "sunrise": data.get("sys", {}).get("sunrise"),
                    "sunset": data.get("sys", {}).get("sunset")
                }
                
                # Возвращаем результат в формате системы
                await logger.info(f"Successfully fetched weather for {result['location']['name']}")
                return {
                    "response": {
                        "ok": True,
                        "result": result
                    }
                }
        
        except httpx.HTTPError as e:
            await logger.error(f"HTTP error during API request: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP error: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
