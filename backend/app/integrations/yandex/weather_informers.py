"""Yandex Weather Get Informers интеграция используя httpx библиотеку."""
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


class YandexGetInformersIntegration(BaseIntegration):
    """
    ИНТЕГРАЦИЯ: YandexGetInformersIntegration
    
    Назначение: Получение данных погоды в формате информеров/виджетов от Яндекс.Погоды
    Эндпоинт: GET /v2/informers - оптимизирован для веб-виджетов
    Особенности: Возвращает готовые иконки, упрощенные данные для быстрого отображения
    """
    
    @property
    def metadata(self) -> IntegrationMetadata:
        """
        МЕТАДАННЫЕ ИНТЕГРАЦИИ ДЛЯ GET INFORMERS
        
        Отличия от forecast:
        - Более простая конфигурация (только lat, lon, lang)
        - Возвращает данные в формате виджетов
        - Включает готовые URL иконок
        """
        return IntegrationMetadata(
            # Базовые идентификаторы
            id="yandex_get_informers",          # Уникальный ID для информеров
            version="1.0.0",
            name="Yandex Get Informers",        # Отображаемое имя в UI
            description="Получение данных погоды в формате информеров/виджетов с готовыми иконками",
            
            # Категоризация (та же категория weather)
            category="weather",
            icon_s3_key="icons/integrations/yandex.svg",  # Используем ту же иконку
            color="#ffcc00",                     # Тот же цвет для консистентности
            
            # СХЕМА КОНФИГУРАЦИИ ДЛЯ INFORMERS
            # Проще чем у forecast - только основные параметры
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],      # Обязательные координаты
                "properties": {
                    "lat": {
                        "type": "number",
                        "title": "Широта",
                        "description": "Географическая широта места",
                        "minimum": -90,
                        "maximum": 90,
                        "examples": [55.7558, 59.9343]
                    },
                    "lon": {
                        "type": "number", 
                        "title": "Долгота",
                        "description": "Географическая долгота места",
                        "minimum": -180,
                        "maximum": 180,
                        "examples": [37.6176, 30.3351]
                    },
                    "lang": {
                        "type": "string",
                        "title": "Язык ответа",
                        "description": "Язык текстовых описаний и названий",
                        "enum": ["ru_RU", "ru_UA", "uk_UA", "be_BY", "kk_KZ", "tr_TR", "en_US"],
                        "default": "ru_RU"
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Количество дней",
                        "description": "Количество дней для прогноза (1-7)",
                        "minimum": 1,
                        "maximum": 7,
                        "default": 1
                    }
                    # Для informers НЕ нужны hours и extra параметры
                }
            },
            
            # НАСТРОЙКИ АВТОРИЗАЦИИ
            # Используем те же credentials что и для forecast
            credentials_provider="other",         # "other" - Другой провайдер в UI
            credentials_strategy="api_key",       # API ключ Яндекс.Погоды
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            
            # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
            examples=[
                {
                    "title": "Информер погоды для Москвы",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6176,
                        "lang": "ru_RU",
                        "limit": 3
                    },
                    "description": "Получить данные для виджета погоды в Москве на 3 дня"
                },
                {
                    "title": "Информер для сайта в СПб",
                    "config": {
                        "lat": 59.9343,
                        "lon": 30.3351,
                        "lang": "ru_RU",
                        "limit": 1
                    },
                    "description": "Данные для однодневного виджета в Санкт-Петербурге"
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
        ГЛАВНЫЙ МЕТОД ДЛЯ GET INFORMERS
        
        Особенности:
        1. Использует эндпоинт /v2/informers вместо /v2/forecast
        2. Получает данные в формате оптимизированном для виджетов
        3. Возвращает готовые URL иконок и упрощенные данные
        """
        
        # ========== ШАГ 1: ПРОВЕРКА БИБЛИОТЕКИ ==========
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }
        
        # ========== ШАГ 2: ПОЛУЧЕНИЕ API КЛЮЧА ==========
        # Используем те же credentials что и для forecast
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",          # Ищем credentials с провайдером "other"
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
        
        # Извлекаем payload с API ключом
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        # Ищем API ключ (такая же логика как в forecast)
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
        
        # ========== ШАГ 3: ПОЛУЧЕНИЕ И ВАЛИДАЦИЯ ПАРАМЕТРОВ ==========
        # Параметры для informers проще чем для forecast
        lat = config.get("lat")
        lon = config.get("lon")
        lang = config.get("lang", "ru_RU")
        limit = config.get("limit", 1)  # По умолчанию 1 день
        
        # Валидация (такая же как в forecast)
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
        
        # ========== ШАГ 4: ВЫПОЛНЕНИЕ HTTP ЗАПРОСА К /v2/informers ==========
        """
        КЛЮЧЕВОЕ ОТЛИЧИЕ: Используем endpoint /v2/informers
        Этот endpoint специально оптимизирован для виджетов
        """
        try:
            # URL для GET INFORMERS (отличается от forecast)
            url = "https://api.weather.yandex.ru/v2/informers"
            
            # Параметры запроса для informers
            params = {
                "lat": lat,
                "lon": lon,
                "lang": lang,
                "limit": limit
                # Для informers НЕ передаются hours и extra
            }
            
            # Заголовки (те же что и для forecast)
            headers = {
                "X-Yandex-Weather-Key": api_key,  # Важно: тот же заголовок
                "User-Agent": "DBCV-Integration/1.0",
                "Accept": "application/json"
            }
            
            # Асинхронный HTTP запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    # УСПЕХ: Получаем данные информеров
                    informers_data = response.json()
                    
                    # Форматируем специфично для informers
                    formatted_result = self._format_informers_response(informers_data)
                    
                    await logger.info(f"Successfully fetched weather informers for lat={lat}, lon={lon}")
                    
                    # Возвращаем результат
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
                    
        # ========== ШАГ 5: ОБРАБОТКА ИСКЛЮЧЕНИЙ ==========
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
    
    def _format_informers_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ФОРМАТИРОВАНИЕ ОТВЕТА ДЛЯ INFORMERS
        
        Ключевые отличия от forecast:
        1. Данные уже частично структурированы для виджетов
        2. Включает готовые URL иконок
        3. Упрощенные прогнозы
        4. Готовые HTML/CSS сниппеты (если есть в API)
        
        Структура ответа informers (пример):
        {
            "now": {текущая погода},
            "forecasts": [упрощенный прогноз],
            "info": {информация о месте},
            "yesterday": {вчерашняя погода для сравнения}
        }
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "latitude": data.get("info", {}).get("lat"),
                "longitude": data.get("info", {}).get("lon"),
                "tz_offset": data.get("info", {}).get("tzinfo", {}).get("offset"),
                "name": data.get("info", {}).get("name", ""),  # Название места
                "url": data.get("info", {}).get("url", "")
            },
            "current": {},
            "forecast": [],
            "yesterday": {},  # Специфично для informers
            "widget_data": {}  # Данные для виджетов
        }
        
        # ТЕКУЩАЯ ПОГОДА (now)
        now = data.get("fact", {}) or data.get("now", {})
        if now:
            result["current"] = {
                "temp": now.get("temp"),
                "feels_like": now.get("feels_like"),
                "condition": now.get("condition"),
                "icon": now.get("icon"),  # ✅ URL иконки для виджета
                "wind_speed": now.get("wind_speed"),
                "wind_dir": now.get("wind_dir"),
                "pressure_mm": now.get("pressure_mm"),
                "humidity": now.get("humidity"),
                "daytime": now.get("daytime"),
                "season": now.get("season")
            }
        
        # ПРОГНОЗ НА ДНИ (forecast) - упрощенный
        forecasts = data.get("forecasts", [])
        for forecast in forecasts:
            day_forecast = {
                "date": forecast.get("date"),
                "sunrise": forecast.get("sunrise"),
                "sunset": forecast.get("sunset"),
                "parts": {}
            }
            
            # Упрощенные данные по частям дня
            parts = forecast.get("parts", {})
            for part_name, part_data in parts.items():
                day_forecast["parts"][part_name] = {
                    "temp": part_data.get("temp_avg") or part_data.get("temp"),  # Упрощенно
                    "temp_min": part_data.get("temp_min"),
                    "temp_max": part_data.get("temp_max"),
                    "condition": part_data.get("condition"),
                    "icon": part_data.get("icon"),  # ✅ URL иконки
                    "wind_speed": part_data.get("wind_speed"),
                    "prec_prob": part_data.get("prec_prob")
                }
            
            result["forecast"].append(day_forecast)
        
        # ВЧЕРАШНЯЯ ПОГОДА (специфично для informers)
        yesterday = data.get("yesterday", {})
        if yesterday:
            result["yesterday"] = {
                "temp": yesterday.get("temp"),
                "condition": yesterday.get("condition")
            }
        
        # ДАННЫЕ ДЛЯ ВИДЖЕТОВ (если есть в ответе)
        if "widget" in data or "widget_data" in data:
            widget_data = data.get("widget") or data.get("widget_data") or {}
            result["widget_data"] = {
                "html": widget_data.get("html", ""),
                "css": widget_data.get("css", ""),
                "js": widget_data.get("js", ""),
                "width": widget_data.get("width"),
                "height": widget_data.get("height")
            }
        
        return result
    
    def _parse_api_error(self, response) -> str:
        """
        ПАРСИНГ ОШИБОК API (такой же как в forecast)
        """
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