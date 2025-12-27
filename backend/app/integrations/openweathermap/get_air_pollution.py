"""OpenWeatherMap Get Air Pollution интеграция используя httpx для прямых HTTP запросов."""
from typing import Dict, Any, Optional
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
        """Возвращает метаданные интеграции."""
        return IntegrationMetadata(
            id="openweathermap_get_air_pollution",
            version="1.0.0",
            name="OpenWeatherMap Get Air Pollution",
            description="Получение данных о загрязнении воздуха (AQI) через OpenWeatherMap Air Pollution API",
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
                    "start": {
                        "type": "integer",
                        "title": "Start Time",
                        "description": "Начало периода в Unix timestamp (секунды). Если не указан, возвращаются текущие данные.",
                        "minimum": 0
                    },
                    "end": {
                        "type": "integer",
                        "title": "End Time",
                        "description": "Конец периода в Unix timestamp (секунды). Используется вместе с 'start'.",
                        "minimum": 0
                    }
                },
                "additionalProperties": False
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Текущее загрязнение воздуха в Москве",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6176
                    },
                    "description": "Получить текущий индекс качества воздуха (AQI) для Москвы"
                },
                {
                    "title": "Загрязнение воздуха в Пекине",
                    "config": {
                        "lat": 39.9042,
                        "lon": 116.4074
                    },
                    "description": "Получить текущий AQI для Пекина"
                },
                {
                    "title": "Исторические данные загрязнения",
                    "config": {
                        "lat": 40.7128,
                        "lon": -74.0060,
                        "start": 1672531200,  # 1 января 2023
                        "end": 1672617600     # 2 января 2023
                    },
                    "description": "Получить исторические данные загрязнения воздуха для Нью-Йорка"
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
        Выполняет интеграцию для получения данных о загрязнении воздуха.
        Использует эндпоинт /air_pollution (текущие или исторические данные).
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
            
        Примеры:
            >>> # Текущие данные
            >>> result = await integration.execute({
            ...     "lat": 55.7558,
            ...     "lon": 37.6176
            ... })
            
            >>> # Исторические данные
            >>> result = await integration.execute({
            ...     "lat": 40.7128,
            ...     "lon": -74.0060,
            ...     "start": 1672531200,
            ...     "end": 1672617600
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
            start = config.get("start")
            end = config.get("end")

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

            # Формируем параметры запроса
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key
            }

            # Добавляем временные параметры, если указаны
            if start is not None:
                params["start"] = start
                if end is not None:
                    params["end"] = end
                else:
                    # Если указан start без end, API вернёт ошибку
                    await logger.error("end parameter is required when start is specified")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 400,
                            "description": "end parameter is required when start is specified"
                        }
                    }

            # ИСПОЛЬЗУЕМ HTTPX ДЛЯ ПРЯМЫХ HTTP ЗАПРОСОВ
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/air_pollution",
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
                                "list": data.get("list", []),
                                "count": len(data.get("list", []))
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