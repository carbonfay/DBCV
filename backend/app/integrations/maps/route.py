"""Google Maps Route интеграция используя googlemaps библиотеку."""
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


class GoogleMapsRouteIntegration(BaseIntegration):
    """Интеграция для получения маршрута через Google Maps API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_route",
            version="1.0.0",
            name="Google Maps Route",
            description="Получение маршрута между двумя точками через Google Maps Directions API",
            category="maps",
            icon_s3_key="icons/integrations/google-maps.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "required": ["origin", "destination"],
                "properties": {
                    "origin": {
                        "type": "string",
                        "title": "Origin",
                        "description": "Начальная точка маршрута (адрес или координаты)"
                    },
                    "destination": {
                        "type": "string",
                        "title": "Destination",
                        "description": "Конечная точка маршрута (адрес или координаты)"
                    },
                    "mode": {
                        "type": "string",
                        "title": "Mode",
                        "description": "Вид транспорта",
                        "enum": ["driving", "walking", "bicycling", "transit"],
                        "default": "driving"
                    },
                    "waypoints": {
                        "type": "array",
                        "title": "Waypoints",
                        "description": "Промежуточные точки маршрута",
                        "items": {
                            "type": "string"
                        }
                    },
                    "departure_time": {
                        "type": "string",
                        "title": "Departure Time",
                        "description": "Время отправления (в формате Unix Timestamp или now)"
                    },
                    "arrival_time": {
                        "type": "string",
                        "title": "Arrival Time",
                        "description": "Время прибытия (в формате Unix Timestamp)"
                    },
                    "traffic_model": {
                        "type": "string",
                        "title": "Traffic Model",
                        "description": "Модель пробок",
                        "enum": ["best_guess", "pessimistic", "optimistic"],
                        "default": "best_guess"
                    },
                    "transit_mode": {
                        "type": "array",
                        "title": "Transit Mode",
                        "description": "Виды транспорта для транзита",
                        "items": {
                            "type": "string",
                            "enum": ["bus", "rail", "subway", "train", "tram"]
                        }
                    },
                    "avoid": {
                        "type": "array",
                        "title": "Avoid",
                        "description": "Чего избегать",
                        "items": {
                            "type": "string",
                            "enum": ["tolls", "highways", "ferries", "indoor"]
                        }
                    },
                    "units": {
                        "type": "string",
                        "title": "Units",
                        "description": "Единицы измерения",
                        "enum": ["metric", "imperial"],
                        "default": "metric"
                    },
                    "language": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык результатов",
                        "default": "ru"
                    }
                }
            },
            credentials_provider="google_maps",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLEMAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить автомобильный маршрут",
                    "config": {
                        "origin": "Москва, Красная площадь",
                        "destination": "Москва, ВДНХ",
                        "mode": "driving"
                    }
                },
                {
                    "title": "Получить пеший маршрут с промежуточными точками",
                    "config": {
                        "origin": "Москва, Тверская улица",
                        "destination": "Москва, Китай-город",
                        "waypoints": ["Москва, Пушкинская площадь"],
                        "mode": "walking"
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
        origin = config.get("origin")
        destination = config.get("destination")
        mode = config.get("mode", "driving")
        waypoints = config.get("waypoints", [])
        departure_time = config.get("departure_time")
        arrival_time = config.get("arrival_time")
        traffic_model = config.get("traffic_model")
        transit_mode = config.get("transit_mode")
        avoid = config.get("avoid")
        units = config.get("units", "metric")
        language = config.get("language", "ru")

        if not origin or not destination:
            await logger.error("origin and destination are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "origin and destination are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем клиент Google Maps
            gmaps = googlemaps.Client(key=api_key)

            # Подготовим параметры для API вызова
            directions_params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "units": units,
                "language": language
            }

            if waypoints:
                directions_params["waypoints"] = waypoints
            if departure_time:
                directions_params["departure_time"] = departure_time
            if arrival_time:
                directions_params["arrival_time"] = arrival_time
            if traffic_model:
                directions_params["traffic_model"] = traffic_model
            if transit_mode:
                directions_params["transit_mode"] = transit_mode
            if avoid:
                directions_params["avoid"] = avoid

            # Запрашиваем направления
            directions_result = gmaps.directions(**directions_params)

            if not directions_result:
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": f"No route found from {origin} to {destination}"
                    }
                }

            # Извлекаем данные маршрута
            routes = []
            for route in directions_result:
                route_summary = {
                    "summary": route.get("summary", ""),
                    "legs": [],
                    "overview_polyline": route.get("overview_polyline", {}).get("points", ""),
                    "bounds": route.get("bounds", {}),
                    "copyrights": route.get("copyrights", ""),
                    "warnings": route.get("warnings", []),
                    "waypoint_order": route.get("waypoint_order", [])
                }

                for leg in route.get("legs", []):
                    leg_summary = {
                        "start_address": leg.get("start_address"),
                        "end_address": leg.get("end_address"),
                        "start_location": leg.get("start_location", {}),
                        "end_location": leg.get("end_location", {}),
                        "distance": leg.get("distance", {}),
                        "duration": leg.get("duration", {}),
                        "duration_in_traffic": leg.get("duration_in_traffic", {}),
                        "arrival_time": leg.get("arrival_time", {}),
                        "departure_time": leg.get("departure_time", {}),
                        "steps": []
                    }

                    for step in leg.get("steps", []):
                        step_summary = {
                            "html_instructions": step.get("html_instructions"),
                            "distance": step.get("distance", {}),
                            "duration": step.get("duration", {}),
                            "start_location": step.get("start_location", {}),
                            "end_location": step.get("end_location", {}),
                            "polyline": step.get("polyline", {}).get("points", ""),
                            "travel_mode": step.get("travel_mode")
                        }
                        leg_summary["steps"].append(step_summary)

                    route_summary["legs"].append(leg_summary)

                routes.append(route_summary)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "routes": routes,
                        "total_routes": len(routes)
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

