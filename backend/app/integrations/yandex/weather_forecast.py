"""Yandex Weather Get Forecast интеграция используя httpx библиотеку."""
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import httpx
    import json
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class YandexGetForecastIntegration(BaseIntegration):
    """Интеграция для получения прогноза погоды от Yandex Weather API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_get_forecast",
            version="1.0.0",
            name="Yandex Get Forecast",
            description="Получение текущей погоды и прогноза на несколько дней от Yandex Weather API",
            category="weather",
            icon_s3_key="icons/integrations/yandex.svg",
            color="#ffcc00",
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {
                        "type": "number",
                        "title": "Широта",
                        "description": "Географическая широта места (например: 55.7558)",
                        "minimum": -90,
                        "maximum": 90,
                        "examples": [55.7558, 59.9343]
                    },
                    "lon": {
                        "type": "number", 
                        "title": "Долгота",
                        "description": "Географическая долгота места (например: 37.6176)",
                        "minimum": -180,
                        "maximum": 180,
                        "examples": [37.6176, 30.3351]
                    },
                    "lang": {
                        "type": "string",
                        "title": "Язык ответа",
                        "description": "Язык текстовых описаний погоды",
                        "enum": ["ru_RU", "ru_UA", "uk_UA", "be_BY", "kk_KZ", "tr_TR", "en_US"],
                        "default": "ru_RU"
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Количество дней прогноза",
                        "description": "Количество дней прогноза (1-7)",
                        "minimum": 1,
                        "maximum": 7,
                        "default": 1
                    },
                    "hours": {
                        "type": "boolean",
                        "title": "Почасовой прогноз",
                        "description": "Включить почасовой прогноз на ближайшие часы",
                        "default": True
                    },
                    "extra": {
                        "type": "boolean",
                        "title": "Детальный прогноз",
                        "description": "Полный детальный прогноз с расширенной информацией",
                        "default": False
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Текущая погода в Москве",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6176,
                        "lang": "ru_RU",
                        "limit": 1,
                        "hours": True
                    }
                },
                {
                    "title": "Прогноз на неделю в Санкт-Петербурге",
                    "config": {
                        "lat": 59.9343,
                        "lon": 30.3351,
                        "lang": "ru_RU", 
                        "limit": 7,
                        "hours": False,
                        "extra": True
                    }
                },
                {
                    "title": "Погода в Сочи на завтра",
                    "config": {
                        "lat": 43.5855,
                        "lon": 39.7231,
                        "lang": "ru_RU",
                        "limit": 2,
                        "hours": True
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
        Выполняет интеграцию используя библиотеку httpx для запросов к Yandex Weather API.
        
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
        
        # Получаем API ключ из credentials (как в примере Telegram)
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Yandex Weather credentials not found")
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
        
        # Ищем API ключ в различных возможных полях
        api_key = (payload.get("api_key") or payload.get("key") or 
                  payload.get("token") or payload.get("yandex_api_key"))
        
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
        lat = config.get("lat")
        lon = config.get("lon")
        lang = config.get("lang", "ru_RU")
        limit = config.get("limit", 1)
        hours = config.get("hours", True)
        extra = config.get("extra", False)
        
        # Валидация параметров (как в Telegram примере)
        if lat is None or lon is None:
            await logger.error("lat and lon are required parameters")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "lat and lon are required parameters"
                }
            }
        
        if not (-90 <= lat <= 90):
            await logger.error(f"Invalid latitude: {lat}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "latitude must be between -90 and 90"
                }
            }
        
        if not (-180 <= lon <= 180):
            await logger.error(f"Invalid longitude: {lon}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "longitude must be between -180 and 180"
                }
            }
        
        if not (1 <= limit <= 7):
            await logger.error(f"Invalid limit: {limit}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "limit must be between 1 and 7"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ httpx НАПРЯМУЮ
        try:
            # Yandex Weather API URL
            url = "https://api.weather.yandex.ru/v2/forecast"
            
            # Параметры запроса
            params = {
                "lat": lat,
                "lon": lon,
                "lang": lang,
                "limit": limit,
                "hours": "true" if hours else "false",
                "extra": "true" if extra else "false"
            }
            
            # Заголовки с API ключом
            headers = { 
                "X-Yandex-Weather-Key": api_key,
                "User-Agent": "DBCV-Integration/1.0",
                "Accept": "application/json"
            }
            
            # Выполняем HTTP запрос (асинхронно, как в SAFE_LIBRARIES.md рекомендациях)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers
                )
                
                # Обработка ответа
                if response.status_code == 200:
                    weather_data = response.json()
                    
                    # Форматируем результат для удобства использования
                    formatted_result = self._format_weather_response(weather_data)
                    
                    await logger.info(f"Successfully fetched weather data for lat={lat}, lon={lon}")
                    
                    return {
                        "response": {
                            "ok": True,
                            "result": formatted_result
                        }
                    }
                else:
                    # Обработка ошибок API
                    error_message = self._parse_api_error(response)
                    await logger.error(f"Yandex Weather API error: {error_message}")
                    
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": error_message,
                            "details": response.text[:500] if response.text else None
                        }
                    }
                    
        except httpx.TimeoutException as e:
            await logger.error(f"Request timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": f"Request timeout: {str(e)}"
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 503,
                    "description": f"HTTP request failed: {str(e)}"
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
    
    def _format_weather_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирует ответ Yandex Weather API в удобный формат."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "latitude": data.get("info", {}).get("lat"),
                "longitude": data.get("info", {}).get("lon"),
                "tz_offset": data.get("info", {}).get("tzinfo", {}).get("offset"),
                "tz_name": data.get("info", {}).get("tzinfo", {}).get("name"),
                "url": data.get("info", {}).get("url")
            },
            "current": {},
            "forecast": []
        }
        
        # Текущая погода (fact)
        fact = data.get("fact", {})
        if fact:
            result["current"] = {
                "temp": fact.get("temp"),
                "feels_like": fact.get("feels_like"),
                "condition": fact.get("condition"),
                "condition_code": fact.get("condition_code"),
                "wind_speed": fact.get("wind_speed"),
                "wind_gust": fact.get("wind_gust"),
                "wind_dir": fact.get("wind_dir"),
                "pressure_mm": fact.get("pressure_mm"),
                "pressure_pa": fact.get("pressure_pa"),
                "humidity": fact.get("humidity"),
                "daytime": fact.get("daytime"),
                "polar": fact.get("polar"),
                "season": fact.get("season"),
                "obs_time": fact.get("obs_time"),
                "prec_type": fact.get("prec_type"),
                "prec_strength": fact.get("prec_strength"),
                "cloudness": fact.get("cloudness"),
                "phenom_condition": fact.get("phenom_condition"),
                "phenom_icon": fact.get("phenom_icon")
            }
        
        # Прогноз на дни
        forecasts = data.get("forecasts", [])
        for forecast in forecasts:
            day_forecast = {
                "date": forecast.get("date"),
                "sunrise": forecast.get("sunrise"),
                "sunset": forecast.get("sunset"),
                "moon_code": forecast.get("moon_code"),
                "moon_text": forecast.get("moon_text"),
                "parts": {},
                "hours": []
            }
            
            # Части дня (утро, день, вечер, ночь)
            parts = forecast.get("parts", {})
            for part_name, part_data in parts.items():
                day_forecast["parts"][part_name] = {
                    "temp_min": part_data.get("temp_min"),
                    "temp_max": part_data.get("temp_max"),
                    "temp_avg": part_data.get("temp_avg"),
                    "feels_like": part_data.get("feels_like"),
                    "condition": part_data.get("condition"),
                    "condition_code": part_data.get("condition_code"),
                    "wind_speed": part_data.get("wind_speed"),
                    "wind_gust": part_data.get("wind_gust"),
                    "wind_dir": part_data.get("wind_dir"),
                    "pressure_mm": part_data.get("pressure_mm"),
                    "pressure_pa": part_data.get("pressure_pa"),
                    "humidity": part_data.get("humidity"),
                    "prec_mm": part_data.get("prec_mm"),
                    "prec_period": part_data.get("prec_period"),
                    "prec_prob": part_data.get("prec_prob"),
                    "prec_type": part_data.get("prec_type"),
                    "prec_strength": part_data.get("prec_strength"),
                    "cloudness": part_data.get("cloudness"),
                    "phenom_condition": part_data.get("phenom_condition"),
                    "phenom_icon": part_data.get("phenom_icon")
                }
            
            # Почасовой прогноз
            hours = forecast.get("hours", [])
            if hours:
                for hour_data in hours:
                    day_forecast["hours"].append({
                        "hour": hour_data.get("hour"),
                        "temp": hour_data.get("temp"),
                        "feels_like": hour_data.get("feels_like"),
                        "condition": hour_data.get("condition"),
                        "condition_code": hour_data.get("condition_code"),
                        "wind_speed": hour_data.get("wind_speed"),
                        "wind_gust": hour_data.get("wind_gust"),
                        "wind_dir": hour_data.get("wind_dir"),
                        "pressure_mm": hour_data.get("pressure_mm"),
                        "humidity": hour_data.get("humidity"),
                        "prec_mm": hour_data.get("prec_mm"),
                        "prec_prob": hour_data.get("prec_prob"),
                        "prec_type": hour_data.get("prec_type"),
                        "prec_strength": hour_data.get("prec_strength"),
                        "cloudness": hour_data.get("cloudness"),
                        "phenom_condition": hour_data.get("phenom_condition"),
                        "phenom_icon": hour_data.get("phenom_icon")
                    })
            
            result["forecast"].append(day_forecast)
        
        return result
    
    def _parse_api_error(self, response) -> str:
        """Парсит ошибку API и возвращает понятное сообщение."""
        status_messages = {
            400: "Неверные параметры запроса",
            401: "Неверный или отсутствующий API ключ",
            403: "Доступ запрещен. Проверьте API ключ",
            404: "Запрошенный ресурс не найден",
            429: "Превышен лимит запросов",
            500: "Внутренняя ошибка сервера Yandex",
            502: "Плохой шлюз",
            503: "Сервис временно недоступен",
            504: "Таймаут шлюза"
        }
        
        default_message = f"HTTP ошибка {response.status_code}"
        
        # Пытаемся получить детали ошибки из JSON
        if response.text:
            try:
                error_data = json.loads(response.text)
                if isinstance(error_data, dict):
                    message = error_data.get("message") or error_data.get("reason") or error_data.get("error")
                    if message:
                        return f"{status_messages.get(response.status_code, default_message)}: {message}"
            except:
                pass
        
        return status_messages.get(response.status_code, default_message)