"""Google Maps Directions Integration for DBCV Platform."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку googlemaps НАПРЯМУЮ в backend код
try:
    import googlemaps
    GOOGLEMAPS_AVAILABLE = True
except ImportError:
    GOOGLEMAPS_AVAILABLE = False
    googlemaps = None


class GoogleMapsDirectionsIntegration(BaseIntegration):
    """Интеграция для получения маршрутов через Google Maps Directions API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_directions",
            version="1.0.0",
            name="Google Maps Directions",
            description="Получение маршрутов через Google Maps Directions API с поддержкой различных режимов передвижения и дополнительных параметров",
            category="maps",
            icon_s3_key="icons/integrations/google.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "required": ["origin", "destination"],
                "properties": {
                    "origin": {
                        "type": "string",
                        "title": "Origin",
                        "description": "Точка отправления (адрес, place_id или lat,lng). Пример: '13.7563,100.5018' или 'place_id:ChIJ...'"
                    },
                    "destination": {
                        "type": "string",
                        "title": "Destination",
                        "description": "Точка назначения (адрес, place_id или lat,lng)"
                    },
                    "mode": {
                        "type": "string",
                        "title": "Travel Mode",
                        "enum": ["driving", "walking", "bicycling", "transit"],
                        "default": "driving",
                        "description": "Режим маршрута"
                    },
                    "waypoints": {
                        "type": "string",
                        "title": "Waypoints",
                        "description": "Промежуточные точки. Формат: 'optimize:true|lat,lng|lat,lng'"
                    },
                    "alternatives": {
                        "type": "boolean",
                        "title": "Alternatives",
                        "description": "Возвращать альтернативные маршруты"
                    },
                    "avoid": {
                        "type": "string",
                        "title": "Avoid",
                        "enum": ["tolls", "highways", "ferries", "indoor"],
                        "description": "Что избегать на маршруте"
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "enum": ["metric", "imperial"],
                        "default": "metric",
                        "description": "Единицы измерения (по умолчанию metric)"
                    },
                    "language": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык ответа (например 'ru', 'en', 'th')"
                    },
                    "region": {
                        "type": "string",
                        "title": "Region",
                        "description": "Региональный bias (например 'th', 'ru')"
                    },
                    "departure_time": {
                        "type": ["integer", "string"],
                        "title": "Departure Time",
                        "description": "Время отправления (Unix timestamp или 'now')"
                    },
                    "arrival_time": {
                        "type": "integer",
                        "title": "Arrival Time",
                        "description": "Время прибытия (Unix timestamp, только для transit)"
                    },
                    "traffic_model": {
                        "type": "string",
                        "title": "Traffic Model",
                        "enum": ["best_guess", "pessimistic", "optimistic"],
                        "description": "Модель трафика (только для driving + departure_time)"
                    },
                    "transit_mode": {
                        "type": "string",
                        "title": "Transit Mode",
                        "enum": ["bus", "subway", "train", "tram", "rail"],
                        "description": "Тип транспорта (только для mode=transit)"
                    },
                    "transit_routing_preference": {
                        "type": "string",
                        "title": "Transit Routing Preference",
                        "enum": ["less_walking", "fewer_transfers"],
                        "description": "Предпочтения маршрута (только для transit)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLEMAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Маршрут на машине",
                    "config": {
                        "origin": "13.7563,100.5018",
                        "destination": "13.7367,100.5231",
                        "mode": "driving"
                    }
                },
                {
                    "title": "Пеший маршрут с промежуточными точками",
                    "config": {
                        "origin": "place_id:ChIJ...",
                        "destination": "place_id:ChIJ...",
                        "mode": "walking",
                        "waypoints": "optimize:true|13.75,100.50|13.74,100.52"
                    }
                },
                {
                    "title": "Общественный транспорт с временем отправления",
                    "config": {
                        "origin": "Москва",
                        "destination": "Тула",
                        "mode": "transit",
                        "departure_time": "now",
                        "transit_mode": "bus"
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
                    "description": "googlemaps library is not installed. Install it with: pip install googlemaps>=4.10.0"
                }
            }
        
        # Пробуем получить credentials из разных комбинаций (для максимальной гибкости)
        creds = None
        used_provider = None
        used_strategy = None
        
        # Варианты для попытки (в порядке приоритета)
        provider_strategy_combos = [
            ("other", "api_key"),
            ("google", "oauth"),
            ("google", "api_key"),
        ]
        
        for provider, strategy in provider_strategy_combos:
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider=provider,
                strategy=strategy
            )
            if creds:
                used_provider = provider
                used_strategy = strategy
                await logger.info(f"Found credentials: provider={provider}, strategy={strategy}")
                break
        
        if not creds:
            await logger.error("Google API key not found for any provider/strategy combination")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google API key not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        # Извлекаем API key или access token в зависимости от стратегии
        api_key = None
        if used_strategy == "oauth":
            api_key = payload.get("access_token")
        else:
            api_key = payload.get("api_key")
        
        if not api_key:
            await logger.error(f"API key/token not found for strategy {used_strategy}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key/token not found in credentials payload"
                }
            }
        
        try:
            # Создаем клиент googlemaps
            gmaps = googlemaps.Client(key=api_key)
            
            # Формируем параметры для directions API
            directions_kwargs = {
                "origin": config["origin"],
                "destination": config["destination"],
                "mode": config.get("mode", "driving"),
                "units": config.get("units", "metric"),
            }
            
            # Добавляем опциональные параметры
            optional_params = [
                "waypoints", "alternatives", "avoid", "units", "language", "region",
                "departure_time", "arrival_time", "traffic_model", "transit_mode", 
                "transit_routing_preference"
            ]
            
            for param in optional_params:
                if param in config and config[param] is not None:
                    directions_kwargs[param] = config[param]
            
            # Логируем запрос
            await logger.info(f"Google Maps Directions request: {directions_kwargs}")
            
            # Вызываем directions API
            result = gmaps.directions(**directions_kwargs)
            
            # Проверяем результат
            if not result:
                await logger.warning("Google Maps Directions returned empty result")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": "No routes found"
                    }
                }
            
            await logger.info(f"Google Maps Directions success: {len(result)} routes found")
            
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "status": "OK",
                        "routes": result
                    }
                }
            }
            
        except googlemaps.exceptions.ApiError as e:
            await logger.error(f"Google Maps API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Google Maps API error: {str(e)}"
                }
            }
        except googlemaps.exceptions.Timeout as e:
            await logger.error(f"Google Maps timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 408,
                    "description": "Request timeout"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error in Google Maps Directions: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Internal error: {str(e)}"
                }
            }
