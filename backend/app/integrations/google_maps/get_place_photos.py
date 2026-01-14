"""Google Maps Get Place Photos интеграция используя googlemaps библиотеку."""
from typing import Dict, Any
from uuid import UUID
from urllib.parse import urlencode

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


class GoogleMapsGetPlacePhotosIntegration(BaseIntegration):
    """Интеграция для получения фотографий места через Google Maps Places API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_get_place_photos",
            version="1.0.0",
            name="Google Maps Get Place Photos",
            description="Получение фотографий места по place_id или поисковому запросу",
            category="maps",
            icon_s3_key="icons/integrations/google_maps.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "properties": {
                    "place_id": {
                        "type": "string",
                        "title": "Place ID",
                        "description": "Идентификатор места в Google Maps (обязателен, если не задан query)"
                    },
                    "query": {
                        "type": "string",
                        "title": "Query",
                        "description": "Поисковый запрос для места (обязателен, если не задан place_id)"
                    },
                    "max_photos": {
                        "type": "integer",
                        "title": "Max Photos",
                        "description": "Максимальное количество фотографий для получения",
                        "minimum": 1,
                        "default": 1
                    },
                    "max_width": {
                        "type": "integer",
                        "title": "Max Width",
                        "description": "Максимальная ширина фотографии в пикселях",
                        "minimum": 1,
                        "maximum": 1600
                    },
                    "max_height": {
                        "type": "integer",
                        "title": "Max Height",
                        "description": "Максимальная высота фотографии в пикселях",
                        "minimum": 1,
                        "maximum": 1600
                    }
                },
                "oneOf": [
                    {"required": ["place_id"]},
                    {"required": ["query"]}
                ]
            },
            credentials_provider="google_maps",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLEMAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Получение фотографий по place_id",
                    "config": {
                        "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                        "max_photos": 3
                    }
                },
                {
                    "title": "Поиск места и получение фотографий",
                    "config": {
                        "query": "Эйфелева башня, Париж",
                        "max_photos": 5,
                        "max_width": 800
                    }
                },
                {
                    "title": "Фотографии с ограничением размера",
                    "config": {
                        "query": "Statue of Liberty",
                        "max_photos": 2,
                        "max_width": 1200,
                        "max_height": 800
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
        place_id = config.get("place_id")
        query = config.get("query")
        max_photos = config.get("max_photos", 1)
        max_width = config.get("max_width")
        max_height = config.get("max_height")
        
        # Валидация параметров
        if not place_id and not query:
            await logger.error("Either place_id or query must be provided")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Either 'place_id' or 'query' must be provided"
                }
            }
        
        if max_photos < 1:
            await logger.error("max_photos must be at least 1")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "max_photos must be at least 1"
                }
            }
        
        if max_width is not None and (max_width < 1 or max_width > 1600):
            await logger.error("max_width must be between 1 and 1600")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "max_width must be between 1 and 1600"
                }
            }
        
        if max_height is not None and (max_height < 1 or max_height > 1600):
            await logger.error("max_height must be between 1 and 1600")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "max_height must be between 1 and 1600"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем клиент Google Maps
            gmaps = googlemaps.Client(key=api_key)
            
            # Если передан query, сначала находим место
            if query and not place_id:
                # Используем Text Search (find_place или places) для поиска места
                places_result = gmaps.find_place(
                    input=query,
                    input_type="textquery",
                    fields=["place_id", "name"]
                )
                
                if not places_result.get("candidates"):
                    await logger.error(f"Place not found for query: {query}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Place not found for query: {query}"
                        }
                    }
                
                # Берем первый результат
                place_id = places_result["candidates"][0]["place_id"]
                await logger.info(f"Found place_id {place_id} for query: {query}")
            
            # Получаем детали места с фотографиями
            place_details = gmaps.place(
                place_id=place_id,
                fields=["photos", "name", "place_id"]
            )
            
            if "result" not in place_details:
                await logger.error(f"Place details not found for place_id: {place_id}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": f"Place details not found for place_id: {place_id}"
                    }
                }
            
            place_result = place_details["result"]
            photos = place_result.get("photos", [])
            
            if not photos:
                await logger.error(f"No photos available for place_id: {place_id}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": f"No photos available for this place"
                    }
                }
            
            # Ограничиваем количество фотографий
            photos = photos[:max_photos]
            
            # Формируем URL фотографий используя стандартный формат Google Maps Places API
            # Библиотека googlemaps не предоставляет специального метода для получения URL фотографий,
            # но мы используем библиотеку для получения place details с photo_reference,
            # а затем формируем URL согласно официальной документации Google Maps API
            photo_results = []
            for photo in photos:
                photo_reference = photo.get("photo_reference")
                if not photo_reference:
                    continue
                
                # Формируем URL фотографии согласно Google Maps Places API Photo
                # Это стандартный способ работы с фотографиями, который используется
                # даже при работе с библиотекой googlemaps
                photo_params = {
                    "photo_reference": photo_reference,
                    "key": api_key
                }
                
                if max_width:
                    photo_params["maxwidth"] = max_width
                if max_height:
                    photo_params["maxheight"] = max_height
                
                # Создаем URL для доступа к фотографии
                # Это не HTTP-запрос, а формирование URL, который клиенты будут использовать
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?{urlencode(photo_params)}"
                
                photo_info = {
                    "photo_reference": photo_reference,
                    "url": photo_url,
                    "width": photo.get("width"),
                    "height": photo.get("height"),
                    "attributions": photo.get("html_attributions", [])
                }
                
                # Добавляем параметры размера, если они были указаны
                if max_width:
                    photo_info["requested_max_width"] = max_width
                if max_height:
                    photo_info["requested_max_height"] = max_height
                
                photo_results.append(photo_info)
            
            if not photo_results:
                await logger.error("No valid photos could be retrieved")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": "No valid photos could be retrieved"
                    }
                }
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "place_id": place_id,
                        "place_name": place_result.get("name"),
                        "photos": photo_results,
                        "count": len(photo_results),
                        "requested_max": max_photos
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

