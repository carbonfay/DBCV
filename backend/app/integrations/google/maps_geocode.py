"""Google Maps Geocode integration using googlemaps library."""
from typing import Any, Dict, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from googlemaps import Client
    from googlemaps.exceptions import ApiError, TransportError, Timeout, HTTPError
    GOOGLE_MAPS_AVAILABLE = True
except ImportError:
    Client = None

    class ApiError(Exception):
        """Fallback ApiError when googlemaps is not installed."""

    class TransportError(Exception):
        """Fallback TransportError when googlemaps is not installed."""

    class Timeout(Exception):
        """Fallback Timeout when googlemaps is not installed."""

    class HTTPError(Exception):
        """Fallback HTTPError when googlemaps is not installed."""

    GOOGLE_MAPS_AVAILABLE = False


def _extract_api_key(creds: Optional[Dict[str, Any]]) -> Optional[str]:
    if not creds:
        return None
    payload = creds.get("payload")
    if not payload:
        payload = creds
    if not isinstance(payload, dict):
        return None
    value = payload.get("api_key")
    if value:
        return str(value)
    return None


def _compact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _classify_api_error(status: Optional[str]) -> str:
    if not status:
        return "api_error"
    status_upper = str(status).upper()
    if status_upper in {"REQUEST_DENIED", "API_KEY_INVALID", "INVALID_KEY"}:
        return "authorization_error"
    if status_upper in {"OVER_QUERY_LIMIT", "OVER_DAILY_LIMIT", "OVER_RATE_LIMIT"}:
        return "quota_error"
    if status_upper in {"INVALID_REQUEST", "MISSING_QUERY", "INVALID_ARGUMENT"}:
        return "validation_error"
    return "api_error"


def _error_response(
    error_type: str,
    message: str,
    status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "type": error_type,
        "message": message,
    }
    if status:
        payload["status"] = status
    if details:
        payload["details"] = details
    return {"response": {"ok": False, "error": payload}}


class GoogleMapsGeocodeIntegration(BaseIntegration):
    """Integration for Google Maps Geocoding API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_geocode",
            version="1.0.0",
            name="Google Maps Geocode",
            description="Geocode addresses using Google Maps Geocoding API",
            category="maps",
            icon_s3_key="icons/integrations/google_maps.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "title": "Google Maps Geocode",
                "description": "Geocoding by address",
                "properties": {
                    "address": {
                        "type": "string",
                        "title": "Address",
                        "description": "Address to geocode",
                    },
                },
                "required": ["address"],
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLE_MAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Geocode address",
                    "config": {
                        "address": "Paris",
                    },
                },
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        if not GOOGLE_MAPS_AVAILABLE:
            await logger.error("googlemaps library is not available")
            return _error_response(
                "dependency_error",
                "googlemaps library is not installed",
            )

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key",
        )
        api_key = _extract_api_key(creds)
        if not api_key:
            await logger.error("Google Maps API key not found")
            return _error_response(
                "credentials_error",
                "Google Maps API key not found in credentials",
            )

        address = config.get("address")
        if not address:
            await logger.error("address is required")
            return _error_response(
                "validation_error",
                "address is required",
            )

        try:
            client = Client(key=api_key)
            results = client.geocode(
                address=address,
            )
            request = _compact_dict(
                {
                    "mode": "geocode",
                    "address": address,
                }
            )

            return {
                "response": {
                    "ok": True,
                    "result": {
                        "request": request,
                        "status": "OK",
                        "results": results,
                        "raw": {
                            "status": "OK",
                            "results": results,
                        },
                    },
                }
            }
        except ApiError as e:
            status = getattr(e, "status", None)
            error_type = _classify_api_error(status)
            await logger.error(f"Google Maps API error: {e}")
            return _error_response(
                error_type,
                str(e),
                status=status,
            )
        except (TransportError, Timeout, HTTPError) as e:
            await logger.error(f"Google Maps transport error: {e}")
            return _error_response(
                "transport_error",
                str(e),
            )
        except Exception as e:
            await logger.error(f"Unexpected Google Maps error: {e}")
            return _error_response(
                "unexpected_error",
                str(e),
            )
