"""Google Maps Get Place Details интеграция через googlemaps SDK."""
import asyncio
import importlib
from typing import Any, Dict, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Динамически импортируем SDK, чтобы не падать, если пакет не установлен
try:
    googlemaps_module = importlib.import_module("googlemaps")
    GoogleMapsClient = getattr(googlemaps_module, "Client")
    exceptions_module = importlib.import_module("googlemaps.exceptions")
    GOOGLE_MAPS_ERRORS = tuple(
        getattr(exceptions_module, name, Exception)
        for name in ("ApiError", "TransportError", "Timeout")
    )
    GOOGLE_MAPS_AVAILABLE = True
except (ImportError, AttributeError):
    GoogleMapsClient = None
    GOOGLE_MAPS_ERRORS = (Exception,)
    GOOGLE_MAPS_AVAILABLE = False


class GoogleMapsGetPlaceDetailsIntegration(BaseIntegration):
    """Получает подробности о месте по place_id."""

    DEFAULT_FIELDS: List[str] = [
        "name",
        "formatted_address",
        "rating",
        "formatted_phone_number",
        "international_phone_number",
        "opening_hours",
        "website",
        "geometry",
        "url",
        "user_ratings_total",
        "price_level",
    ]

    @staticmethod
    def _failure(description: str, error_code: int) -> Dict[str, Any]:
        return {
            "response": {
                "ok": False,
                "error_code": error_code,
                "description": description,
            }
        }

    def _normalize_fields(self, raw_fields: Any) -> List[str]:
        """Приводим поля из config к списку строк с сохранением порядка."""
        if raw_fields is None:
            return list(self.DEFAULT_FIELDS)
        if isinstance(raw_fields, str):
            raw_fields = [part.strip() for part in raw_fields.split(",") if part.strip()]
        elif isinstance(raw_fields, list):
            raw_fields = [str(item).strip() for item in raw_fields if str(item).strip()]
        else:
            return list(self.DEFAULT_FIELDS)
        if not raw_fields:
            return list(self.DEFAULT_FIELDS)
        # Удаляем дубликаты, сохраняя порядок
        return list(dict.fromkeys(raw_fields))

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_get_place_details",
            version="1.0.0",
            name="Google Maps Get Place Details",
            description="Возвращает подробную информацию о месте через Google Places API",
            category="maps",
            icon_s3_key="icons/integrations/google_maps.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "required": ["place_id"],
                "properties": {
                    "place_id": {
                        "type": "string",
                        "title": "Place ID",
                        "description": "Идентификатор места в Google Maps (например, ChIJN1t_tDeuEmsRUsoyG83frY4)",
                    },
                    "fields": {
                        "type": "array",
                        "title": "Fields",
                        "items": {"type": "string"},
                        "description": "Какие поля вернуть (см. документацию Places API)",
                        "default": self.DEFAULT_FIELDS,
                    },
                    "language": {
                        "type": "string",
                        "title": "Language",
                        "description": "Код языка (например, ru, en)",
                    },
                },
            },
            credentials_provider="google_maps",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLE_MAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Минимальный запрос",
                    "config": {"place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"},
                },
                {
                    "title": "Кастомные поля",
                    "config": {
                        "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                        "fields": ["name", "geometry", "opening_hours", "rating"],
                        "language": "ru",
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
        if not GOOGLE_MAPS_AVAILABLE or GoogleMapsClient is None:
            await logger.error("googlemaps library is not available")
            return self._failure("googlemaps library is not installed", 500)

        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="google_maps",
            strategy="api_key",
        )

        if not creds:
            await logger.error("Google Maps credentials not found")
            return self._failure("Google Maps API key not found in credentials", 401)

        payload = creds.get("payload") or creds
        api_key = payload.get("api_key") or payload.get("key")
        if not api_key:
            await logger.error(f"api_key not found in credentials. Keys: {list(payload.keys())}")
            return self._failure("api_key not found in credentials", 401)

        place_id = config.get("place_id")
        if not place_id:
            await logger.error("place_id is required")
            return self._failure("place_id is required", 400)

        fields = self._normalize_fields(config.get("fields"))
        language = config.get("language")

        client = GoogleMapsClient(key=str(api_key))
        try:
            # googlemaps.Client.place синхронный, поэтому выполняем его в thread pool
            response = await asyncio.to_thread(
                client.place,
                place_id=str(place_id),
                fields=fields if fields else None,
                language=str(language) if language else None,
            )
        except GOOGLE_MAPS_ERRORS as exc:  # type: ignore[arg-type]
            await logger.error(f"Google Maps error: {exc}")
            return self._failure(str(exc), 502)
        except Exception as exc:
            await logger.error(f"Unexpected Google Maps error: {exc}")
            return self._failure(str(exc), 500)

        if not isinstance(response, dict):
            await logger.error("Unexpected response type from googlemaps Client.place")
            return self._failure("Unexpected response from Google Maps API", 502)

        status = response.get("status", "UNKNOWN")
        if status != "OK":
            error_message = response.get("error_message") or f"Google Maps API returned status {status}"
            # Мапим статусы API на HTTP-коды платформы, чтобы фронту было проще
            status_code_map = {
                "ZERO_RESULTS": 404,
                "NOT_FOUND": 404,
                "INVALID_REQUEST": 400,
                "REQUEST_DENIED": 403,
                "OVER_QUERY_LIMIT": 429,
            }
            await logger.error(f"Google Maps returned error: {status} ({error_message})")
            return self._failure(error_message, status_code_map.get(status, 502))

        place_data = response.get("result") or {}
        await logger.info(f"Fetched place details for {place_data.get('place_id', place_id)}")
        return {
            "response": {
                "ok": True,
                "result": {
                    "status": status,
                    "place_id": place_data.get("place_id") or place_id,
                    "requested_fields": fields,
                    "place": place_data,
                },
            }
        }

