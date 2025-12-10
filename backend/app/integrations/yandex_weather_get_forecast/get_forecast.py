"""Яндекс.Погода Get Forecast интеграция используя httpx (v0.27.x) для HTTP запросов."""
from typing import Dict, Any
from uuid import UUID
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
import inspect


async def _maybe_await_logger(logger: BotLogger, method: str, *args):
    """Call logger.method(*args) and await result only if it's awaitable.

    This makes the integration robust when tests supply a MagicMock
    (which is not awaitable) or an AsyncMock (which is awaitable).
    """
    fn = getattr(logger, method, None)
    if not fn:
        return
    try:
        res = fn(*args)
        if inspect.isawaitable(res):
            await res
    except Exception:
        # We deliberately swallow logger exceptions to avoid failing the integration
        return

# Импортируем httpx для HTTP запросов
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class YandexWeatherGetForecastIntegration(BaseIntegration):
    """Интеграция для получения прогноза погоды через Яндекс.Погода API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_weather_get_forecast",
            version="1.0.0",
            name="Yandex Weather Get Forecast",
            description="Получение прогноза погоды из Яндекс.Погода с поддержкой гео-координат и различных типов данных",
            category="weather",
            icon_s3_key="icons/integrations/yandex_weather.svg",
            color="#0066CC",
            config_schema={
                "type": "object",
                "required": ["latitude", "longitude"],
                "properties": {
                    "latitude": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Широта местоположения (от -90 до 90)"
                    },
                    "longitude": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Долгота местоположения (от -180 до 180)"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "enum": ["en_US", "en_GB", "ru_RU", "uk_UA", "be_BY", "kk_KZ", "tr_TR"],
                        "default": "en_US",
                        "description": "Язык текста погоды"
                    },
                    "extra": {
                        "type": "boolean",
                        "title": "Extra Data",
                        "default": False,
                        "description": "Получить дополнительные данные (feels_like, uv_index и т.д.)"
                    },
                    "hours": {
                        "type": "boolean",
                        "title": "Hourly Data",
                        "default": False,
                        "description": "Вернуть почасовой прогноз вместо дневного"
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Days Limit",
                        "default": 7,
                        "description": "Количество дней прогноза (1..7)"
                    }
                }
            },
            credentials_provider="yandex_weather",
            credentials_strategy="api_key",
            library_name=("httpx==0.27.*" if HTTPX_AVAILABLE else None),
            examples=[
                {
                    "title": "Погода в Москве",
                    "config": {
                        "latitude": 55.75,
                        "longitude": 37.62,
                        "lang": "ru_RU",
                        "extra": False
                    }
                },
                {
                    "title": "Подробная погода в Санкт-Петербурге",
                    "config": {
                        "latitude": 59.93,
                        "longitude": 30.33,
                        "lang": "ru_RU",
                        "extra": True,
                        "hours": True,
                        "limit": 3
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
        Выполняет интеграцию используя httpx для запросов к Яндекс.Погода API.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not HTTPX_AVAILABLE:
            await _maybe_await_logger(logger, "error", "httpx library is not available")
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
            provider="yandex_weather",
            strategy="api_key"
        )
        
        if not creds:
            await _maybe_await_logger(logger, "error", "Yandex Weather credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Yandex Weather API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("token")
        if not api_key:
            await _maybe_await_logger(logger, "error", f"api_key not found in credentials. Available keys: {list(payload.keys())}")
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
        lang = config.get("lang", "en_US")
        extra = config.get("extra", False)
        hours = config.get("hours", False)
        limit = config.get("limit", 7)
        
        # Валидация параметров
        if latitude is None or longitude is None:
            await _maybe_await_logger(logger, "error", "latitude and longitude are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "latitude and longitude are required"
                }
            }
        
        # Проверяем диапазоны координат
        if not (-90 <= latitude <= 90):
            await _maybe_await_logger(logger, "error", f"Invalid latitude: {latitude}. Must be between -90 and 90")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid latitude: {latitude}. Must be between -90 and 90"
                }
            }
        
        if not (-180 <= longitude <= 180):
            await _maybe_await_logger(logger, "error", f"Invalid longitude: {longitude}. Must be between -180 and 180")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid longitude: {longitude}. Must be between -180 and 180"
                }
            }
        
        # Валидация limit
        try:
            limit = int(limit)
        except Exception:
            await _maybe_await_logger(logger, "error", f"Invalid limit value: {limit}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "limit must be an integer (1..7)"
                }
            }

        if not (1 <= limit <= 7):
            await logger.error(f"Invalid limit: {limit}. Must be between 1 and 7")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid limit: {limit}. Must be between 1 and 7"
                }
            }

        # ИСПОЛЬЗУЕМ HTTPX НАПРЯМУЮ ДЛЯ ЗАПРОСА К ЯНДЕКС.ПОГОДА API
        try:
            # Яндекс.Погода API endpoint
            url = "https://api.weather.yandex.ru/v2/forecast"
            
            # Параметры запроса
            params = {
                "lat": latitude,
                "lon": longitude,
                "lang": lang,
                "extra": "true" if extra else "false",
                "hours": "true" if hours else "false",
                "limit": limit
            }
            
            # Headers с API ключом
            headers = {
                "X-Yandex-API-Key": api_key,
                "User-Agent": "DBCV/1.0"
            }
            
            # Выполняем HTTP GET запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
            
            # Проверяем статус ответа
            if response.status_code == 200:
                data = response.json()
                
                # Возвращаем результат в формате системы
                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "now": data.get("now"),
                            "now_dt": data.get("now_dt"),
                            "forecasts": data.get("forecasts"),
                            "info": {
                                "lat": data.get("info", {}).get("lat"),
                                "lon": data.get("info", {}).get("lon"),
                                "url": data.get("info", {}).get("url"),
                                "def_pressure_type": data.get("info", {}).get("def_pressure_type"),
                                "def_temp_accuracy": data.get("info", {}).get("def_temp_accuracy")
                            }
                        }
                    }
                }
            elif response.status_code == 401:
                await _maybe_await_logger(logger, "error", f"Invalid API key: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "Invalid Yandex Weather API key"
                    }
                }
            elif response.status_code == 403:
                await _maybe_await_logger(logger, "error", f"Access forbidden: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 403,
                        "description": "Access forbidden (check API key and permissions)"
                    }
                }
            elif response.status_code == 429:
                await _maybe_await_logger(logger, "error", f"Rate limit exceeded: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 429,
                        "description": "Rate limit exceeded (too many requests)"
                    }
                }
            else:
                await _maybe_await_logger(logger, "error", f"HTTP error {response.status_code}: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"Yandex Weather API error: {response.text[:200]}"
                    }
                }
        
        except httpx.TimeoutException as e:
            await _maybe_await_logger(logger, "error", f"Timeout error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 408,
                    "description": "Request timeout (Yandex Weather API is not responding)"
                }
            }
        
        except httpx.RequestError as e:
            await _maybe_await_logger(logger, "error", f"Request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Network error: {str(e)}"
                }
            }
        
        except ValueError as e:
            await _maybe_await_logger(logger, "error", f"JSON decode error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "Invalid response from Yandex Weather API"
                }
            }
        
        except Exception as e:
            await _maybe_await_logger(logger, "error", f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }
