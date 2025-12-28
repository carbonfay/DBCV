"""Google Maps Get Place Details интеграция используя googlemaps библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку
try:
    import googlemaps
    from googlemaps.exceptions import ApiError, TransportError, Timeout
    GOOGLEMAPS_AVAILABLE = True
except ImportError:
    GOOGLEMAPS_AVAILABLE = False
    googlemaps = None
    ApiError = Exception
    TransportError = Exception
    Timeout = Exception


class GooglePlaceDetailsIntegration(BaseIntegration):
    """Интеграция для получения детальной информации о месте через Google Maps Places API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_place_details",
            version="1.0.0",
            name="Google Maps Get Place Details",
            description="Получение детальной информации о месте по place_id через Google Maps Places API",
            category="maps",
            icon_s3_key="icons/integrations/google_maps.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "required": ["place_id", "fields"],
                "properties": {
                    "place_id": {
                        "type": "string",
                        "title": "Place ID",
                        "description": "Идентификатор места в Google Maps (place_id)"
                    },
                    "fields": {
                        "type": "string",
                        "title": "Fields",
                        "description": "Поля через запятую. Доступные варианты:\nname - наименование места\nformatted_address - полный адрес\ngeometry - координаты (lat, lng)\nrating - рейтинг места\nwebsite - веб-сайт\nformatted_phone_number - номер телефона\nopening_hours - часы работы\nurl - URL места на Google Maps\nbusiness_status - статус бизнеса (OPERATIONAL, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY)\nadr_address - адрес в микроформате\nplace_id - ID места\n\nПримеры: 'name,formatted_address,rating' или 'name,website,formatted_phone_number'"
                    },
                    "language": {
                        "type": "string",
                        "title": "Language",
                        "description": "Код языка (ru, en, th и т.д.)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLEMAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Основная информация по place_id",
                    "config": {
                        "place_id": "ChIJybDUc_xKtUYRTM9XV8zWRD0",
                        "fields": "name,formatted_address,geometry"
                    }
                },
                {
                    "title": "Полная информация",
                    "config": {
                        "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
                        "fields": "name,formatted_address,rating,website,formatted_phone_number,opening_hours",
                        "language": "ru"
                    }
                },
                {
                    "title": "Контактные данные",
                    "config": {
                        "place_id": "ChIJ5x6lWkpfy0YRFY1sxbKkwr0",
                        "fields": "name,website,formatted_phone_number,opening_hours",
                        "language": "ru",
                    }
                },
                {
                    "title": "Минимальный запрос",
                    "config": {
                        "place_id": "ChIJdUyx15R95kcRj85ZX8H8OAU",
                        "fields": "name,formatted_address"
                    }
                },
                {
                    "title": "Все доступные поля: name (имя места), formatted_address (полный адрес), geometry (координаты), rating (рейтинг), website (сайт), formatted_phone_number (телефон), opening_hours (часы работы), url (ссылка Google Maps), business_status (статус), adr_address (адрес микроформат), place_id (ID места)",
                    "config": {
                        "place_id": "ChIJ51cu8IcbXWARiRtXIothAS4",
                        "fields": "name,formatted_address,geometry,rating,website,formatted_phone_number,opening_hours,url,business_status,adr_address,place_id",
                        "language": "en"
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
        
        # Получаем Google API key из credentials (пробуем несколько провайдеров)
        creds = None
        used_provider = None
        
        for provider in [ "other", "google" ]:
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider=provider,
                strategy="api_key"
            )
            if creds:
                used_provider = provider
                await logger.info(f"Found credentials for provider: {provider}")
                break
        
        if not creds:
            await logger.error("Google Maps credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google Maps API key not found in credentials"
                }
            }
        
        # Извлекаем API key из credentials
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        api_key = payload.get("api_key")
        if not api_key:
            await logger.error("api_key not found in Google credentials payload")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials payload"
                }
            }
        
        try:
            # Создаем клиент Google Maps
            gmaps = googlemaps.Client(key=api_key)
            
            # Берем place_id напрямую из конфига (поддерживаем camelCase и snake_case)
            place_id = str(config.get("place_id") or config.get("placeId") or "").strip()
            if not place_id:
                raise ValueError("place_id is required")
            
            # Парсим fields (может быть массив или строка)
            fields_input = config.get("fields")
            if not fields_input:
                raise ValueError("fields parameter is required")
            
            # Если это массив, используем как есть; если строка, разбиваем по запятым
            if isinstance(fields_input, list):
                fields = [f.strip() if isinstance(f, str) else f for f in fields_input]
            else:
                fields = [f.strip() for f in str(fields_input).split(",") if f.strip()]
            
            if not fields:
                raise ValueError("At least one field must be specified")
            
            place_kwargs = {
                "place_id": place_id,
                "fields": fields,
            }
            
            # Добавляем опциональные параметры
            if "language" in config and config["language"]:
                place_kwargs["language"] = config["language"]
            # if "region" in config and config["region"]:
            #     place_kwargs["region"] = config["region"]
            
            await logger.info(f"Getting place details for place_id={place_id}, fields={fields}")
            
            # Вызываем Google Maps Places API
            result = gmaps.place(**place_kwargs)
            
            # Проверяем статус ответа
            if result.get("status") != "OK":
                await logger.error(f"Google Places API error: {result.get('status')}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": result.get("status", "UNKNOWN_ERROR")
                    }
                }
            
            # Извлекаем данные места
            place_data = result.get("result", {})
            
            await logger.info(f"Place details retrieved successfully for {place_data.get('name', place_id)}")
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": place_data
                }
            }
            
        except ValueError as e:
            await logger.error(f"ValueError: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": str(e)
                }
            }
        except ApiError as e:
            await logger.error(f"Google Maps ApiError: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": str(e)
                }
            }
        except TransportError as e:
            await logger.error(f"Google Maps TransportError: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "Network connection error"
                }
            }
        except Timeout as e:
            await logger.error(f"Google Maps Timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": "Request timeout"
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
