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
            description="Получение ежедневного прогноза погоды на 1-16 дней через OpenWeatherMap Daily Forecast API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#f1603d",
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],  # Изменено: отдельные поля вместо location
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
                        "maximum": 16,  # Изменено: максимум 16 дней вместо 7
                        "description": "Количество дней прогноза (максимум 16, по умолчанию 7)"
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "enum": ["standard", "metric", "imperial"],  # Изменено: стандартные значения OpenWeatherMap
                        "default": "metric",
                        "description": "Единицы измерения (standard - Кельвин, metric - Цельсий, imperial - Фаренгейт)"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "default": "en",  # Изменено: английский по умолчанию
                        "description": "Язык ответа (en, ru, и т.д.)"
                    }
                }
            },
            credentials_provider="openweathermap",
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
                },
                {
                    "title": "Прогноз на неделю для Лондона",
                    "config": {
                        "lat": 51.5074,
                        "lon": -0.1278,
                        "cnt": 7,
                        "units": "metric",
                        "lang": "en"
                    }
                },
                {
                    "title": "Прогноз на 16 дней для Нью-Йорка",
                    "config": {
                        "lat": 40.7128,
                        "lon": -74.0060,
                        "cnt": 16,
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

        # Получаем параметры из config (ИЗМЕНЕНО: отдельные поля lat, lon)
        lat = config.get("lat")
        lon = config.get("lon")
        cnt = config.get("cnt", 7)
        units = config.get("units", "metric")
        lang = config.get("lang", "en")

        # Проверяем обязательные параметры (ИЗМЕНЕНО)
        if lat is None or lon is None:
            await logger.error("lat and lon are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "lat and lon are required parameters"
                }
            }

        # Формируем параметры запроса (ИЗМЕНЕНО: упрощено, т.к. lat и lon уже отдельно)
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "cnt": min(max(1, cnt), 16),  # ИЗМЕНЕНО: максимум 16 вместо 7
            "units": units,
            "lang": lang
        }

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
                    await logger.error(f"Location not found: lat={lat}, lon={lon}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Location not found for coordinates"
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