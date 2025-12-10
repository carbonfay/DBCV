"""Yandex Maps Geocode интеграция для геокодирования адресов и координат."""
import httpx
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class YandexMapsGeocodeIntegration(BaseIntegration):
    """Интеграция для геокодирования через Yandex Maps API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_maps_geocode",
            version="1.0.0",
            name="Yandex Maps Geocode",
            description="Преобразование адресов в координаты и наоборот через Yandex Maps API",
            category="geolocation",
            icon_s3_key="icons/integrations/yandex_maps.svg",
            color="#f8604a",
            config_schema={
                "type": "object",
                "required": ["geocode"],
                "properties": {
                    "geocode": {
                        "type": "string",
                        "title": "Geocode Query",
                        "description": "Адрес или координаты для геокодирования (например: 'Москва, Красная площадь' или '37.6184,55.7512')"
                    },
                    "kind": {
                        "type": "string",
                        "title": "Object Kind",
                        "enum": ["house", "street", "metro", "district", "locality", "province", "country"],
                        "description": "Тип объекта для поиска",
                        "default": None
                    },
                    "results": {
                        "type": "integer",
                        "title": "Results Count",
                        "description": "Количество возвращаемых результатов",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    },
                    "skip": {
                        "type": "integer",
                        "title": "Skip Results",
                        "description": "Количество пропускаемых результатов",
                        "minimum": 0,
                        "default": 0
                    }
                }
            },
            credentials_provider="yandex_maps",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Геокодирование адреса",
                    "config": {
                        "geocode": "Москва, Красная площадь"
                    }
                },
                {
                    "title": "Обратное геокодирование",
                    "config": {
                        "geocode": "37.6184,55.7512",
                        "kind": "house"
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
        Выполняет геокодирование через Yandex Maps API.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        # Получаем api_key из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="yandex_maps",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Yandex Maps credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Yandex Maps API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("key")
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
        geocode_query = config.get("geocode")
        kind = config.get("kind")
        results = config.get("results", 10)
        skip = config.get("skip", 0)
        
        if not geocode_query:
            await logger.error("geocode parameter is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "geocode parameter is required"
                }
            }
        
        # Формируем URL для запроса
        base_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "geocode": geocode_query,
            "format": "json",
            "results": results,
            "skip": skip,
            "apikey": api_key
        }
        
        # Добавляем параметр kind если указан
        if kind:
            params["kind"] = kind
        
        # Выполняем запрос к Yandex Maps API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url, params=params)
                
                if response.status_code != 200:
                    error_text = response.text
                    await logger.error(f"Yandex Maps API error: {response.status_code} - {error_text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": f"Yandex Maps API error: {error_text}"
                        }
                    }
                
                result = response.json()
                
                # Проверяем статус ответа от Yandex
                found_count = result.get("response", {}).get("GeoObjectCollection", {}).get("metaDataProperty", {}).get("GeocoderResponseMetaData", {}).get("found", 0)
                if found_count == 0:
                    await logger.warning("No geocoding results found")
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "found": 0,
                                "features": []
                            }
                        }
                    }
                
                # Возвращаем результат в формате системы
                return {
                    "response": {
                        "ok": True,
                        "result": result
                    }
                }
        
        except httpx.RequestError as e:
            await logger.error(f"HTTP error during Yandex Maps request: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP error: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error during Yandex Maps request: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
