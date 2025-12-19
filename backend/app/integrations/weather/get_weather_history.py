"""OpenWeatherMap Get Weather History интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx
import datetime

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class OpenWeatherMapGetWeatherHistoryIntegration(BaseIntegration):
    """Интеграция для получения исторических данных погоды из OpenWeatherMap API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_weather_history",
            version="1.0.0",
            name="OpenWeatherMap Get Weather History",
            description="Получение исторических данных погоды из OpenWeatherMap API (необходима подписка на исторические данные)",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#5B9BD3",
            config_schema={
                "type": "object",
                "required": ["city", "date"],
                "properties": {
                    "city": {
                        "type": "string",
                        "title": "City",
                        "description": "Название города для получения истории (например, 'London', 'Moscow')"
                    },
                    "date": {
                        "type": "string",
                        "title": "Date",
                        "description": "Дата для получения исторических данных (в формате YYYY-MM-DD или UNIX timestamp)"
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "description": "Единицы измерения температуры",
                        "enum": ["metric", "imperial", "kelvin"],
                        "default": "metric"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык ответа",
                        "default": "en"
                    }
                }
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить исторические данные для Москвы за вчерашний день",
                    "config": {
                        "city": "Moscow, RU",
                        "date": "2023-10-01",
                        "units": "metric"
                    }
                },
                {
                    "title": "Получить исторические данные для Нью-Йорка по timestamp",
                    "config": {
                        "city": "New York, US",
                        "date": "1696185600"  # UNIX timestamp
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
        city = config.get("city")
        date_param = config.get("date")  # может быть датой в формате YYYY-MM-DD или timestamp
        units = config.get("units", "metric")
        lang = config.get("lang", "en")

        if not city or not date_param:
            await logger.error("city and date are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "city and date are required"
                }
            }

        # Преобразуем дату в timestamp
        dt = 0
        try:
            # Проверяем, является ли date_param timestamp (число)
            dt = int(date_param)
        except ValueError:
            # Если нет, пытаемся преобразовать из формата YYYY-MM-DD
            try:
                date_obj = datetime.datetime.strptime(date_param, "%Y-%m-%d")
                dt = int(date_obj.timestamp())
            except ValueError:
                await logger.error(f"Invalid date format: {date_param}. Expected format: YYYY-MM-DD or UNIX timestamp")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"Invalid date format: {date_param}. Expected format: YYYY-MM-DD or UNIX timestamp"
                    }
                }

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # Сначала нужно получить координаты города
            geo_url = "https://api.openweathermap.org/geo/1.0/direct"
            geo_params = {
                "q": city,
                "limit": 1,
                "appid": api_key
            }
            
            # Выполняем запрос для получения координат
            async with httpx.AsyncClient() as client:
                geo_response = await client.get(geo_url, params=geo_params)
                
                if geo_response.status_code != 200:
                    await logger.error(f"OpenWeatherMap Geo API returned status {geo_response.status_code}: {geo_response.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": geo_response.status_code,
                            "description": f"Geo API returned status {geo_response.status_code}: {geo_response.text}"
                        }
                    }
                
                geo_data = geo_response.json()
                if not geo_data or len(geo_data) == 0:
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"City {city} not found"
                        }
                    }
                
                lat = geo_data[0]["lat"]
                lon = geo_data[0]["lon"]

                # Формируем URL для запроса исторических данных
                base_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
                params = {
                    "lat": lat,
                    "lon": lon,
                    "dt": dt,
                    "appid": api_key,
                    "units": units,
                    "lang": lang
                }
                
                response = await client.get(base_url, params=params)

            # Проверяем статус ответа
            if response.status_code != 200:
                if response.status_code == 401:
                    await logger.error(f"Unauthorized. Check your OpenWeatherMap subscription: {response.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 401,
                            "description": f"Unauthorized or subscription required: {response.text}. Historical weather data requires a paid subscription on OpenWeatherMap."
                        }
                    }
                else:
                    await logger.error(f"OpenWeatherMap API returned status {response.status_code}: {response.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": f"API returned status {response.status_code}: {response.text}"
                        }
                    }

            # Парсим JSON-ответ
            data = response.json()

            # Извлекаем исторические данные
            hourly_data = data.get("hourly", [])
            
            # Подготовим данные для ответа
            historical_data = []
            for item in hourly_data:
                historical_item = {
                    "dt": item.get("dt"),
                    "temp": item.get("temp"),
                    "feels_like": item.get("feels_like"),
                    "pressure": item.get("pressure"),
                    "humidity": item.get("humidity"),
                    "dew_point": item.get("dew_point"),
                    "uvi": item.get("uvi"),
                    "clouds": item.get("clouds"),
                    "visibility": item.get("visibility"),
                    "wind_speed": item.get("wind_speed"),
                    "wind_deg": item.get("wind_deg"),
                    "wind_gust": item.get("wind_gust"),
                    "weather": item.get("weather", []),
                    "rain": item.get("rain", {}),
                    "snow": item.get("snow", {})
                }
                historical_data.append(historical_item)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "timezone": data.get("timezone"),
                        "timezone_offset": data.get("timezone_offset"),
                        "requested_dt": dt,
                        "requested_date": datetime.datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S'),
                        "historical_data": historical_data,
                        "count": len(historical_data)
                    }
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

