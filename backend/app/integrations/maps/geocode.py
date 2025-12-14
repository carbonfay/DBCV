"""Google Maps Geocode интеграция используя googlemaps библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import googlemaps
    GOOGLEMAPS_AVAILABLE = True
except ImportError:
    GOOGLEMAPS_AVAILABLE = False
    googlemaps = None


class GoogleMapsGeocodeIntegration(BaseIntegration):
    """Интеграция для геокодирования адресов через Google Maps API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_geocode",
            version="1.0.0",
            name="Google Maps Geocode",
            description="Геокодирование адресов в координаты через Google Maps API",
            category="maps",
            icon_s3_key="icons/integrations/google-maps.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "required": ["address"],
                "properties": {
                    "address": {
                        "type": "string",
                        "title": "Address",
                        "description": "Адрес для геокодирования (например, 'Москва, Красная площадь')"
                    },
                    "components": {
                        "type": "object",
                        "title": "Components",
                        "description": "Фильтр компонентов адреса",
                        "properties": {
                            "country": {
                                "type": "string",
                                "title": "Country",
                                "description": "Код страны (например, 'RU', 'US')"
                            },
                            "administrative_area": {
                                "type": "string",
                                "title": "Administrative Area",
                                "description": "Область/регион"
                            },
                            "locality": {
                                "type": "string",
                                "title": "Locality",
                                "description": "Город"
                            }
                        }
                    },
                    "bounds": {
                        "type": "object",
                        "title": "Bounds",
                        "description": "Ограничивающая рамка для поиска",
                        "properties": {
                            "northeast": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number"},
                                    "lng": {"type": "number"}
                                }
                            },
                            "southwest": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number"},
                                    "lng": {"type": "number"}
                                }
                            }
                        }
                    },
                    "region": {
                        "type": "string",
                        "title": "Region",
                        "description": "Код региона для региональной настройки"
                    },
                    "language": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык результата",
                        "default": "ru"
                    }
                }
            },
            credentials_provider="google_maps",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLEMAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Геокодирование адреса в Москве",
                    "config": {
                        "address": "Москва, Красная площадь, 1",
                        "language": "ru"
                    }
                },
                {
                    "title": "Геокодирование с ограничением по стране",
                    "config": {
                        "address": "Москва",
                        "components": {
                            "country": "RU"
                        }
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
        Выполняет интеграцию используя библиотеку googlemaps.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not GOOGLEMAPS_AVAILABLE:
            await logger.error("googlemaps library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "googlemaps library is not installed"
                }
            }

        # Получаем api_key из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="google_maps",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Google Maps credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google Maps api_key not found in credentials"
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
        address = config.get("address")
        components = config.get("components")
        bounds = config.get("bounds")
        region = config.get("region")
        language = config.get("language", "ru")

        if not address:
            await logger.error("address is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "address is required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем клиент Google Maps
            gmaps = googlemaps.Client(key=api_key)

            # Подготовим параметры для геокодирования
            geocode_params = {
                "address": address,
                "language": language
            }

            if components:
                geocode_params["components"] = components
            if bounds:
                geocode_params["bounds"] = bounds
            if region:
                geocode_params["region"] = region

            # Выполняем геокодирование
            geocode_result = gmaps.geocode(**geocode_params)

            if not geocode_result:
                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "results": [],
                            "status": "ZERO_RESULTS",
                            "summary": "No results found for the given address"
                        }
                    }
                }

            # Подготовим результаты
            results = []
            for result in geocode_result:
                result_entry = {
                    "address_components": [
                        {
                            "long_name": component.get("long_name"),
                            "short_name": component.get("short_name"),
                            "types": component.get("types", [])
                        } for component in result.get("address_components", [])
                    ],
                    "formatted_address": result.get("formatted_address"),
                    "geometry": {
                        "location": result.get("geometry", {}).get("location", {}),
                        "location_type": result.get("geometry", {}).get("location_type"),
                        "viewport": result.get("geometry", {}).get("viewport", {}),
                        "bounds": result.get("geometry", {}).get("bounds")
                    },
                    "place_id": result.get("place_id"),
                    "types": result.get("types", []),
                    "partial_match": result.get("partial_match")
                }
                results.append(result_entry)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "results": results,
                        "status": "OK",
                        "summary": f"Found {len(results)} result(s) for address: {address}"
                    }
                }
            }
        except Exception as e:
            await logger.error(f"Google Maps API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

