"""Google Maps Get Elevation интеграция используя googlemaps библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import googlemaps
    from googlemaps.exceptions import ApiError, HTTPError, Timeout
    GOOGLEMAPS_AVAILABLE = True
except ImportError:
    GOOGLEMAPS_AVAILABLE = False
    googlemaps = None
    ApiError = Exception
    HTTPError = Exception
    Timeout = Exception


class GoogleMapsGetElevationIntegration(BaseIntegration):
    """Интеграция для получения высоты над уровнем моря через Google Maps Elevation API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_get_elevation",
            version="1.0.0",
            name="Google Maps Get Elevation",
            description="Получение высоты над уровнем моря для заданных координат или вдоль пути",
            category="maps",
            icon_s3_key="icons/integrations/google_maps.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "title": "Locations",
                        "description": "Массив координат {lat, lng} для получения высоты (обязателен, если не используется path)",
                        "items": {
                            "type": "object",
                            "required": ["lat", "lng"],
                            "properties": {
                                "lat": {
                                    "type": "number",
                                    "title": "Latitude",
                                    "description": "Широта (-90 до 90)"
                                },
                                "lng": {
                                    "type": "number",
                                    "title": "Longitude",
                                    "description": "Долгота (-180 до 180)"
                                }
                            }
                        },
                        "minItems": 1
                    },
                    "path": {
                        "type": "array",
                        "title": "Path",
                        "description": "Массив координат {lat, lng} для получения высоты вдоль пути (опционально)",
                        "items": {
                            "type": "object",
                            "required": ["lat", "lng"],
                            "properties": {
                                "lat": {
                                    "type": "number",
                                    "title": "Latitude",
                                    "description": "Широта (-90 до 90)"
                                },
                                "lng": {
                                    "type": "number",
                                    "title": "Longitude",
                                    "description": "Долгота (-180 до 180)"
                                }
                            }
                        },
                        "minItems": 2
                    },
                    "samples": {
                        "type": "integer",
                        "title": "Samples",
                        "description": "Количество точек выборки вдоль пути (обязателен при использовании path, минимум 2)",
                        "minimum": 2
                    },
                    "unit": {
                        "type": "string",
                        "title": "Unit",
                        "description": "Единица измерения высоты",
                        "enum": ["meters", "feet"],
                        "default": "meters"
                    }
                },
                "anyOf": [
                    {"required": ["locations"]},
                    {"required": ["path", "samples"]}
                ]
            },
            credentials_provider="google_maps",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLEMAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Высота для одной точки",
                    "config": {
                        "locations": [
                            {"lat": 40.714728, "lng": -73.998672}
                        ],
                        "unit": "meters"
                    }
                },
                {
                    "title": "Высота для нескольких точек",
                    "config": {
                        "locations": [
                            {"lat": 40.714728, "lng": -73.998672},
                            {"lat": 40.758896, "lng": -73.985130}
                        ],
                        "unit": "meters"
                    }
                },
                {
                    "title": "Высота вдоль пути",
                    "config": {
                        "path": [
                            {"lat": 40.714728, "lng": -73.998672},
                            {"lat": 40.758896, "lng": -73.985130}
                        ],
                        "samples": 10,
                        "unit": "meters"
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
        
        # Получаем API key из credentials
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
                    "description": "Google Maps API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("key") or payload.get("token")
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
        locations = config.get("locations")
        path = config.get("path")
        samples = config.get("samples")
        unit = config.get("unit", "meters")
        
        # Валидация параметров
        if not locations and not path:
            await logger.error("Either locations or path must be provided")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Either 'locations' or 'path' must be provided"
                }
            }
        
        if path and not samples:
            await logger.error("samples is required when using path")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "samples is required when using path"
                }
            }
        
        if path and samples < 2:
            await logger.error("samples must be at least 2")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "samples must be at least 2"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем клиент Google Maps
            gmaps = googlemaps.Client(key=api_key)
            
            # Вызываем соответствующий метод в зависимости от параметров
            if path:
                # Получаем высоту вдоль пути
                # Преобразуем path в список кортежей (lat, lng)
                path_tuples = [(point["lat"], point["lng"]) for point in path]
                results = gmaps.elevation_along_path(path_tuples, samples)
            else:
                # Получаем высоту для точек
                # Преобразуем locations в список кортежей (lat, lng)
                locations_tuples = [(point["lat"], point["lng"]) for point in locations]
                results = gmaps.elevation(locations_tuples)
            
            # Преобразуем результаты в нужный формат
            elevation_results = []
            for result in results:
                elevation_data = {
                    "location": {
                        "lat": result["location"]["lat"],
                        "lng": result["location"]["lng"]
                    },
                    "elevation": result["elevation"]
                }
                
                # Конвертируем единицы измерения, если нужно
                if unit == "feet":
                    elevation_data["elevation"] = elevation_data["elevation"] * 3.28084
                
                elevation_results.append(elevation_data)
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "results": elevation_results,
                        "unit": unit,
                        "count": len(elevation_results)
                    }
                }
            }
            
        except ApiError as e:
            await logger.error(f"Google Maps API error: {e}")
            error_code = getattr(e, 'status', 500)
            return {
                "response": {
                    "ok": False,
                    "error_code": error_code,
                    "description": f"Google Maps API error: {str(e)}"
                }
            }
        except HTTPError as e:
            await logger.error(f"HTTP error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP error: {str(e)}"
                }
            }
        except Timeout as e:
            await logger.error(f"Timeout error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": f"Request timeout: {str(e)}"
                }
            }
        except ValueError as e:
            await logger.error(f"Invalid parameter: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Invalid parameter: {str(e)}"
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


