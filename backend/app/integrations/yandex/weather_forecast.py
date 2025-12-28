"""Yandex Weather Forecast интеграция используя httpx для прямых HTTP запросов к Yandex Weather API."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class YandexWeatherForecastIntegration(BaseIntegration):
    """Интеграция для получения прогноза погоды от Yandex Weather API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_weather_forecast",
            version="1.0.1",
            name="Yandex Weather Forecast",
            description="Получение прогноза погоды от Yandex Weather API",
            category="weather",
            icon_s3_key="icons/integrations/yandex.svg",
            color="#ff0000",
            config_schema={
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {
                    "lat": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Широта (от -90 до 90)"
                    },
                    "lon": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Долгота (от -180 до 180)"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "enum": ["ru_RU", "en_US", "uk_UA", "be_BY", "kk_KZ", "tr_TR", "uz_UZ"],
                        "default": "ru_RU",
                        "description": "Язык ответа"
                    },
                    "limit": {
                        "type": "integer",
                        "title": "Limit",
                        "minimum": 1,
                        "maximum": 7,
                        "default": 7,
                        "description": "Количество дней прогноза (1-7)"
                    },
                    "hours": {
                        "type": "boolean",
                        "title": "Include Hours",
                        "default": False,
                        "description": "Включить почасовой прогноз"
                    },
                    "extra": {
                        "type": "boolean",
                        "title": "Extra Info",
                        "default": False,
                        "description": "Дополнительная информация (осадки, ветер, влажность)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Прогноз погоды в Москве",
                    "config": {
                        "lat": 55.7558,
                        "lon": 37.6173,
                        "lang": "ru_RU",
                        "limit": 3,
                        "hours": True,
                        "extra": True
                    }
                },
                {
                    "title": "Простой прогноз",
                    "config": {
                        "lat": 59.9343,
                        "lon": 30.3351,
                        "limit": 1
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
        Выполняет интеграцию используя httpx для запросов к Yandex Weather API.
        
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
        
        # Получаем api_key из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Yandex credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Yandex API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        api_key = payload.get("api_key") or payload.get("token") or payload.get("yandex_api_key")
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
        lat = config.get("lat")
        lon = config.get("lon")
        lang = config.get("lang", "ru_RU")
        limit = config.get("limit", 7)
        hours = config.get("hours", False)
        extra = config.get("extra", False)
        
        if lat is None or lon is None:
            await logger.error("lat and lon are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "lat and lon are required"
                }
            }
        
        # Проверяем диапазоны
        if not (-90 <= lat <= 90):
            await logger.error("lat must be between -90 and 90")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "lat must be between -90 and 90"
                }
            }
        
        if not (-180 <= lon <= 180):
            await logger.error("lon must be between -180 and 180")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "lon must be between -180 and 180"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "lat": lat,
                    "lon": lon,
                    "lang": lang,
                    "limit": limit,
                    "hours": str(hours).lower(),
                    "extra": str(extra).lower()
                }
                
                response = await client.get(
                    "https://api.weather.yandex.ru/v2/forecast",
                    params=params,
                    headers={
                        "X-Yandex-API-Key": api_key
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Возвращаем результат в формате системы
                    return {
                        "response": {
                            "ok": True,
                            "result": data
                        }
                    }
                else:
                    await logger.error(f"Yandex Weather API error: {response.status_code} - {response.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": f"Yandex Weather API error: {response.text}"
                        }
                    }
        except httpx.TimeoutException:
            await logger.error("Request timeout")
            return {
                "response": {
                    "ok": False,
                    "error_code": 408,
                    "description": "Request timeout"
                }
            }
        except httpx.HTTPStatusError as e:
            await logger.error(f"HTTP error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.response.status_code,
                    "description": str(e)
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