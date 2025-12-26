from __future__ import annotations

from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore


class YandexMapsRouteIntegration(BaseIntegration):
    """Интеграция для построения маршрута через Yandex Routing API."""

    _BASE_URL = "https://api.routing.yandex.net/v2/route"

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_maps_route",
            version="1.0.1",
            name="Yandex Maps Route",
            description="Построение маршрута между точками через Yandex Routing API",
            category="maps",
            icon_s3_key="icons/integrations/yandex.svg",
            color="#FFCC00",
            config_schema={
                "type": "object",
                "required": ["origin_lat", "origin_lon", "destination_lat", "destination_lon"],
                "properties": {
                    "origin_lat": {
                        "type": "number",
                        "title": "Origin Latitude",
                        "description": "Широта точки старта (WGS84)"
                    },
                    "origin_lon": {
                        "type": "number",
                        "title": "Origin Longitude",
                        "description": "Долгота точки старта (WGS84)"
                    },
                    "destination_lat": {
                        "type": "number",
                        "title": "Destination Latitude",
                        "description": "Широта точки назначения (WGS84)"
                    },
                    "destination_lon": {
                        "type": "number",
                        "title": "Destination Longitude",
                        "description": "Долгота точки назначения (WGS84)"
                    },
                    "via_points": {
                        "type": "array",
                        "title": "Via Points",
                        "description": "Промежуточные точки маршрута. Формат элементов: {lat, lon}",
                        "items": {
                            "type": "object",
                            "required": ["lat", "lon"],
                            "properties": {
                                "lat": {"type": "number", "title": "Latitude"},
                                "lon": {"type": "number", "title": "Longitude"}
                            }
                        },
                        "default": []
                    },
                    "mode": {
                        "type": "string",
                        "title": "Mode",
                        "description": "Тип маршрута",
                        "enum": ["driving", "truck", "walking", "transit", "bicycle", "scooter"],
                        "default": "driving"
                    },
                    "avoid_tolls": {
                        "type": "boolean",
                        "title": "Avoid Tolls",
                        "description": "Избегать платных дорог (только driving/truck)",
                        "default": False
                    },
                    "traffic": {
                        "type": "string",
                        "title": "Traffic",
                        "description": "Учет пробок (только driving/truck)",
                        "enum": ["default", "disabled"],
                        "default": "default"
                    },
                    "departure_time": {
                        "type": "integer",
                        "title": "Departure Time (UNIX)",
                        "description": "Время отправления в UNIX time (для прогноза пробок)",
                        "default": None
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "title": "Timeout (seconds)",
                        "description": "Таймаут запроса к API",
                        "default": 15
                    },
                    "use_mock": {
                        "type": "boolean",
                        "title": "Use Mock Response",
                        "description": "Если true, интеграция вернет тестовый ответ без вызова Yandex API",
                        "default": False
                    }
                }
            },
            credentials_provider="yandex",
            credentials_strategy="api_key",
            library_name="httpx==0.27.*" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Маршрут на авто (driving)",
                    "config": {
                        "origin_lat": 55.7558,
                        "origin_lon": 37.6173,
                        "destination_lat": 55.751244,
                        "destination_lon": 37.618423,
                        "mode": "driving",
                        "avoid_tolls": False,
                        "traffic": "default"
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }

        use_mock = bool(config.get("use_mock", False))

        if use_mock:
            import math

            def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
                r = 6371000.0
                phi1 = math.radians(lat1)
                phi2 = math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                return int(r * c)

            origin_lat = config.get("origin_lat")
            origin_lon = config.get("origin_lon")
            destination_lat = config.get("destination_lat")
            destination_lon = config.get("destination_lon")
            via_points: List[Dict[str, Any]] = config.get("via_points") or []
            mode = config.get("mode") or "driving"

            if origin_lat is None or origin_lon is None or destination_lat is None or destination_lon is None:
                await logger.error("origin_lat, origin_lon, destination_lat, destination_lon are required")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "origin_lat, origin_lon, destination_lat, destination_lon are required"
                    }
                }

            try:
                origin_lat_f = float(origin_lat)
                origin_lon_f = float(origin_lon)
                destination_lat_f = float(destination_lat)
                destination_lon_f = float(destination_lon)
            except (TypeError, ValueError) as e:
                await logger.error(f"Invalid coordinates: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "Invalid coordinates"
                    }
                }

            points: List[tuple[float, float]] = [(origin_lat_f, origin_lon_f)]
            for p in via_points:
                try:
                    points.append((float(p.get("lat")), float(p.get("lon"))))
                except Exception:
                    continue
            points.append((destination_lat_f, destination_lon_f))

            total_m = 0
            for (la1, lo1), (la2, lo2) in zip(points, points[1:]):
                total_m += _haversine_m(la1, lo1, la2, lo2)

            avg_speed_mps = 11.11 if mode in {"driving", "truck"} else 1.4
            total_s = int(total_m / avg_speed_mps) if total_m > 0 else 0

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "status_code": 200,
                        "summary": {
                            "status": "OK",
                            "mode": mode,
                            "traffic_type": "mock",
                            "legs_count": max(len(points) - 1, 0),
                            "total_length_m": total_m,
                            "total_duration_s": total_s,
                        },
                        "request": {
                            "url": self._BASE_URL,
                            "params": {
                                "apikey": "***",
                                "mode": str(mode),
                                "waypoints": "mock",
                            },
                        },
                        "data": {
                            "mock": True,
                            "status": "OK",
                            "mode": mode,
                            "route": {
                                "legs": [
                                    {
                                        "steps": [
                                            {
                                                "length": total_m,
                                                "duration": total_s,
                                            }
                                        ]
                                    }
                                ]
                            },
                        },
                    },
                }
            }

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="yandex",
            strategy="api_key",
        )

        if not creds:
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="other",
                strategy="api_key",
            )

        if not creds:
            await logger.error("Yandex credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Yandex api_key not found in credentials"
                }
            }

        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        api_key = (
            payload.get("api_key")
            or payload.get("apikey")
            or payload.get("token")
            or payload.get("key")
        )

        if not api_key:
            await logger.error(f"api_key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "api_key not found in credentials"
                }
            }

        origin_lat = config.get("origin_lat")
        origin_lon = config.get("origin_lon")
        destination_lat = config.get("destination_lat")
        destination_lon = config.get("destination_lon")
        via_points: List[Dict[str, Any]] = config.get("via_points") or []

        mode = config.get("mode") or "driving"
        avoid_tolls = bool(config.get("avoid_tolls", False))
        traffic = config.get("traffic") or "default"
        departure_time = config.get("departure_time")
        timeout_seconds = config.get("timeout_seconds", 15)

        if origin_lat is None or origin_lon is None or destination_lat is None or destination_lon is None:
            await logger.error("origin_lat, origin_lon, destination_lat, destination_lon are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "origin_lat, origin_lon, destination_lat, destination_lon are required"
                }
            }

        try:
            origin_lat_f = float(origin_lat)
            origin_lon_f = float(origin_lon)
            destination_lat_f = float(destination_lat)
            destination_lon_f = float(destination_lon)
        except (TypeError, ValueError) as e:
            await logger.error(f"Invalid coordinates: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Invalid coordinates"
                }
            }

        waypoint_parts: List[str] = [f"{origin_lon_f},{origin_lat_f}"]
        for p in via_points:
            lat = p.get("lat")
            lon = p.get("lon")
            if lat is None or lon is None:
                continue
            try:
                lat_f = float(lat)
                lon_f = float(lon)
            except (TypeError, ValueError):
                continue
            waypoint_parts.append(f"{lon_f},{lat_f}")
        waypoint_parts.append(f"{destination_lon_f},{destination_lat_f}")

        params: Dict[str, Any] = {
            "apikey": str(api_key),
            "waypoints": "|".join(waypoint_parts),
            "mode": str(mode),
        }

        if mode in {"driving", "truck"}:
            params["avoid_tolls"] = "true" if avoid_tolls else "false"
            if str(traffic) == "disabled":
                params["traffic"] = "disabled"
            if departure_time is not None:
                try:
                    params["departure_time"] = str(int(departure_time))
                except (TypeError, ValueError):
                    pass

        try:
            timeout = httpx.Timeout(float(timeout_seconds))
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(self._BASE_URL, params=params)

            status_code = response.status_code

            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}

            if status_code >= 400:
                await logger.error(f"Yandex Routing API error: status={status_code}, body={data}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": status_code,
                        "description": "Yandex Routing API error",
                        "result": {
                            "status_code": status_code,
                            "data": data,
                        },
                    }
                }

            summary: Dict[str, Any] = {
                "status": data.get("status"),
                "mode": data.get("mode"),
                "traffic_type": data.get("traffic_type"),
            }

            route = data.get("route") or {}
            legs = route.get("legs") or []
            summary["legs_count"] = len(legs) if isinstance(legs, list) else 0

            total_length_m = 0
            total_duration_s = 0
            if isinstance(legs, list):
                for leg in legs:
                    if not isinstance(leg, dict):
                        continue
                    steps = leg.get("steps") or []
                    if not isinstance(steps, list):
                        continue
                    for step in steps:
                        if not isinstance(step, dict):
                            continue
                        try:
                            total_length_m += int(step.get("length") or 0)
                        except Exception:
                            pass
                        try:
                            total_duration_s += int(step.get("duration") or 0)
                        except Exception:
                            pass

            summary["total_length_m"] = total_length_m
            summary["total_duration_s"] = total_duration_s

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "status_code": status_code,
                        "summary": summary,
                        "request": {
                            "url": self._BASE_URL,
                            "params": {
                                **params,
                                "apikey": "***",
                            },
                        },
                        "data": data,
                    },
                }
            }

        except httpx.TimeoutException as e:
            await logger.error(f"Timeout calling Yandex Routing API: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": "Timeout calling Yandex Routing API",
                }
            }
        except httpx.HTTPError as e:
            await logger.error(f"HTTP error calling Yandex Routing API: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 502,
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
