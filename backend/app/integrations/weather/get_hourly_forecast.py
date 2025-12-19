"""OpenWeatherMap Get Hourly Forecast интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class OpenWeatherMapGetHourlyForecastIntegration(BaseIntegration):
    """Интеграция для получения прогноза погоды на ближайшие 48 часов из OpenWeatherMap API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_hourly_forecast",
            version="1.0.0",
            name="OpenWeatherMap Get Hourly Forecast",
            description="Получение часовго прогноза погоды на ближайшие 48 часов из OpenWeatherMap API",
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
                        "description": "Количество часов в ответе (до 48)",
                        "minimum": 1,
                        "maximum": 48,
                        "default": 12
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
                    "title": "Получить прогноз на 12 часов для Москвы",
                    "config": {
                        "city": "Moscow, RU",
                        "cnt": 12,
                        "units": "metric"
                    }
                },
                {
                    "title": "Получить прогноз на 24 часа для Нью-Йорка",
                    "config": {
                        "city": "New York",
                        "cnt": 24,
                        "units": "imperial"
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
        cnt = config.get("cnt", 12)  # по умолчанию 12 часов
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
            # Формируем URL для запроса к OpenWeatherMap API (OneCall API для прогноза)
            base_url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "q": city,
                "appid": api_key,
                "units": units,
                "lang": lang,
                "cnt": cnt
            }

            # Выполняем GET-запрос
            async with httpx.AsyncClient() as client:
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

            # Извлекаем нужные данные о прогнозе
            forecast_list = data.get("list", [])
            city_info = data.get("city", {})

            hourly_forecasts = []
            for item in forecast_list[:cnt]:  # ограничиваем количеством
                forecast_item = {
                    "dt": item.get("dt"),
                    "dt_txt": item.get("dt_txt"),
                    "main": item.get("main", {}),
                    "weather": item.get("weather", []),
                    "clouds": item.get("clouds", {}),
                    "wind": item.get("wind", {}),
                    "visibility": item.get("visibility"),
                    "pop": item.get("pop"),
                    "sys": item.get("sys", {}),
                    "rain": item.get("rain", {}),
                    "snow": item.get("snow", {})
                }
                hourly_forecasts.append(forecast_item)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "city": {
                            "id": city_info.get("id"),
                            "name": city_info.get("name"),
                            "country": city_info.get("country"),
                            "coord": city_info.get("coord"),
                            "population": city_info.get("population"),
                            "timezone": city_info.get("timezone")
                        },
                        "cod": data.get("cod"),
                        "message": data.get("message"),
                        "cnt": data.get("cnt"),
                        "hourly_forecasts": hourly_forecasts
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

