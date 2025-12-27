"""OpenWeatherMap Get Weather History интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any, Optional
from uuid import UUID
import time

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


class OpenweathermapGetWeatherHistoryIntegration(BaseIntegration):
    """Интеграция для получения исторических данных о погоде через OpenWeatherMap Time Machine API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        """Возвращает метаданные интеграции."""
        return IntegrationMetadata(
            id="openweathermap_get_history",
            version="1.0.0",
            name="OpenWeatherMap Get Weather History",
            description="Получение исторических данных о погоде для указанной даты через OpenWeatherMap Time Machine API",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#f1603d",
            config_schema={
                "type": "object",
                "required": ["lat", "lon", "dt"],
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
                    "dt": {
                        "type": "integer",
                        "title": "Date/Time",
                        "description": "Дата в формате Unix timestamp (секунды с 1 января 1970 UTC). Должна быть в прошлом.",
                        "minimum": 0
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
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Исторические данные для Москвы (вчера)",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6176,
                        "dt": int(time.time() - 86400),  # Вчера
                        "units": "metric",
                        "lang": "ru"
                    },
                    "description": "Получить данные о погоде для Москвы на вчерашний день"
                },
                {
                    "title": "Исторические данные для Лондона (неделю назад)",
                    "config": {
                        "lat": 51.5074,
                        "lon": -0.1278,
                        "dt": int(time.time() - 7 * 86400),  # Неделю назад
                        "units": "metric",
                        "lang": "en"
                    },
                    "description": "Получить данные о погоде для Лондона недельной давности"
                },
                {
                    "title": "Новый Год в Нью-Йорке (2023)",
                    "config": {
                        "lat": 40.7128,
                        "lon": -74.0060,
                        "dt": 1672531200,  # 1 января 2023, 00:00:00 UTC
                        "units": "imperial",
                        "lang": "en"
                    },
                    "description": "Получить погодные данные на Новый Год 2023 в Нью-Йорке"
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
        Выполняет интеграцию для получения исторических данных о погоде.
        Использует эндпоинт /onecall/timemachine (Time Machine API).
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
            
        Примеры:
            >>> # Данные на вчера
            >>> yesterday = int(time.time() - 86400)
            >>> result = await integration.execute({
            ...     "lat": 55.7558,
            ...     "lon": 37.6176,
            ...     "dt": yesterday,
            ...     "units": "metric",
            ...     "lang": "ru"
            ... })
            
            >>> # Конкретная дата
            >>> result = await integration.execute({
            ...     "lat": 40.7128,
            ...     "lon": -74.0060,
            ...     "dt": 1672531200,  # 1 января 2023
            ...     "units": "imperial",
            ...     "lang": "en"
            ... })
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

            # Извлекаем API ключ из credentials
            api_key = None
            
            # Вариант 1: creds - словарь
            if isinstance(creds, dict):
                payload = creds.get("payload", creds)
                if isinstance(payload, dict):
                    api_key = payload.get("api_key") or payload.get("apikey") or payload.get("key")
            
            # Вариант 2: creds - объект с атрибутами
            elif hasattr(creds, 'api_key'):
                api_key = creds.api_key
            elif hasattr(creds, 'apikey'):
                api_key = creds.apikey
            elif hasattr(creds, 'key'):
                api_key = creds.key
            elif hasattr(creds, 'payload'):
                payload = creds.payload
                if hasattr(payload, 'api_key'):
                    api_key = payload.api_key
                elif isinstance(payload, dict):
                    api_key = payload.get("api_key") or payload.get("apikey") or payload.get("key")

            if not api_key:
                await logger.error(f"API key not found in credentials. Type: {type(creds)}")
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
            dt = config.get("dt")
            units = config.get("units", "metric")
            lang = config.get("lang", "en")

            # Проверяем обязательные параметры
            if lat is None or lon is None:
                await logger.error("lat and lon are required")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "lat and lon are required parameters"
                    }
                }

            if dt is None:
                await logger.error("dt (timestamp) is required")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "dt (timestamp) is required parameter"
                    }
                }

            # Дополнительная проверка: dt должен быть в прошлом
            current_time = int(time.time())
            if dt >= current_time:
                await logger.warning(f"Timestamp {dt} is not in the past (current: {current_time}). API may return error.")

            # Формируем параметры запроса
            params = {
                "lat": lat,
                "lon": lon,
                "dt": dt,
                "appid": api_key,
                "units": units,
                "lang": lang
            }

            # ИСПОЛЬЗУЕМ HTTPX ДЛЯ ПРЯМЫХ HTTP ЗАПРОСОВ К TIME MACHINE API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/onecall/timemachine",
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()

                    # Возвращаем результат в формате системы
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "lat": data.get("lat"),
                                "lon": data.get("lon"),
                                "timezone": data.get("timezone"),
                                "timezone_offset": data.get("timezone_offset"),
                                "current": data.get("current", {}),
                                "hourly": data.get("hourly", []),
                                "count": len(data.get("hourly", []))
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
                    
                    # Более информативные сообщения об ошибках для 400
                    if "dt" in error_message.lower():
                        error_message = f"Invalid timestamp (dt): {error_message}"
                    elif "coordinate" in error_message.lower():
                        error_message = f"Invalid coordinates: {error_message}"
                    
                    await logger.error(f"Bad request: {error_message}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": f"Bad request: {error_message}"
                        }
                    }
                elif response.status_code == 429:
                    await logger.error("Rate limit exceeded")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 429,
                            "description": "Rate limit exceeded. Please try again later."
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
        except httpx.HTTPStatusError as e:
            # Обработка HTTP ошибок
            status_code = e.response.status_code if e.response else 500
            await logger.error(f"HTTP error {status_code}: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": status_code,
                    "description": f"HTTP error {status_code}: {str(e)}"
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
                    "description": f"Unexpected error: {str(e)}"
                }
            }