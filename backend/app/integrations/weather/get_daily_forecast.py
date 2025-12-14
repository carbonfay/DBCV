"""OpenWeatherMap Get Daily Forecast интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class OpenWeatherMapGetDailyForecastIntegration(BaseIntegration):
    """Интеграция для получения ежедневного прогноза погоды на 16 дней из OpenWeatherMap API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_daily_forecast",
            version="1.0.0",
            name="OpenWeatherMap Get Daily Forecast",
            description="Получение ежедневного прогноза погоды на 16 дней из OpenWeatherMap API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#5B9BD3",
            config_schema={
                "type": "object",
                "required": ["city"],
                "properties": {
                    "city": {
                        "type": "string",
                        "title": "City",
                        "description": "Название города для получения прогноза (например, 'London', 'Moscow')"
                    },
                    "cnt": {
                        "type": "integer",
                        "title": "Count",
                        "description": "Количество дней в ответе (до 16)",
                        "minimum": 1,
                        "maximum": 16,
                        "default": 7
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
                    "title": "Получить прогноз на 7 дней для Москвы",
                    "config": {
                        "city": "Moscow, RU",
                        "cnt": 7,
                        "units": "metric"
                    }
                },
                {
                    "title": "Получить прогноз на 14 дней для Лондона",
                    "config": {
                        "city": "London, GB",
                        "cnt": 14,
                        "units": "metric"
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
        cnt = config.get("cnt", 7)  # по умолчанию 7 дней
        units = config.get("units", "metric")  # metric, imperial, kelvin
        lang = config.get("lang", "en")  # язык ответа

        if not city:
            await logger.error("city is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "city is required"
                }
            }

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # Используем OneCall API для получения ежедневного прогноза
            base_url = "https://api.openweathermap.org/data/2.5/onecall"
            
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
                
                # Теперь делаем запрос к OneCall API для получения ежедневного прогноза
                params = {
                    "lat": lat,
                    "lon": lon,
                    "appid": api_key,
                    "units": units,
                    "lang": lang,
                    "exclude": "current,minutely,hourly,alerts"  # исключаем ненужные данные, получаем только daily
                }
                
                response = await client.get(base_url, params=params)

            # Проверяем статус ответа
            if response.status_code != 200:
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

            # Извлекаем ежедневные прогнозы
            daily_list = data.get("daily", [])
            
            # Ограничиваем количество дней в соответствии с параметром
            daily_forecasts = []
            for item in daily_list[:cnt]:
                daily_item = {
                    "dt": item.get("dt"),
                    "sunrise": item.get("sunrise"),
                    "sunset": item.get("sunset"),
                    "moonrise": item.get("moonrise"),
                    "moonset": item.get("moonset"),
                    "moon_phase": item.get("moon_phase"),
                    "temp": item.get("temp", {}),
                    "feels_like": item.get("feels_like", {}),
                    "pressure": item.get("pressure"),
                    "humidity": item.get("humidity"),
                    "dew_point": item.get("dew_point"),
                    "wind_speed": item.get("wind_speed"),
                    "wind_deg": item.get("wind_deg"),
                    "wind_gust": item.get("wind_gust"),
                    "weather": item.get("weather", []),
                    "clouds": item.get("clouds"),
                    "pop": item.get("pop"),
                    "uvi": item.get("uvi"),
                    "rain": item.get("rain"),
                    "snow": item.get("snow")
                }
                daily_forecasts.append(daily_item)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "timezone": data.get("timezone"),
                        "timezone_offset": data.get("timezone_offset"),
                        "daily_forecasts": daily_forecasts,
                        "count_requested": cnt,
                        "count_received": len(daily_forecasts)
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

