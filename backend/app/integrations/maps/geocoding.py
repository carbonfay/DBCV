"""Google Maps Geocoding интеграция используя googlemaps библиотеку."""
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


class GoogleMapsGeocodingIntegration(BaseIntegration):
    """Интеграция для геокодирования адресов через Google Maps API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_maps_geocoding",
            version="1.0.0",
            name="Google Maps Geocoding",
            description="Преобразование адресов в координаты (геокодирование) через Google Maps API",
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
                        "description": "Адрес для геокодирования (например, 'Москва, Красная площадь, 1')"
                    }
                }
            },
            credentials_provider="google_maps",
            credentials_strategy="api_key",
            library_name="googlemaps>=4.10.0" if GOOGLEMAPS_AVAILABLE else None,
            examples=[
                {
                    "title": "Геокодирование адреса",
                    "config": {
                        "address": "Москва, Красная площадь, 1"
                    }
                },
                {
                    "title": "Геокодирование с номером дома",
                    "config": {
                        "address": "1600 Amphitheatre Parkway, Mountain View, CA"
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

            # Выполняем геокодирование
            geocode_result = gmaps.geocode(address)

            if not geocode_result:
                # Если результат пустой, возвращаем соответствующую ошибку
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": f"No results found for address: {address}"
                    }
                }

            # Извлекаем нужные данные из результата геокодирования
            result = geocode_result[0]  # Берем первый результат
            location = result.get("geometry", {}).get("location", {})
            
            formatted_result = {
                "formatted_address": result.get("formatted_address"),
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "place_id": result.get("place_id"),
                "types": result.get("types", []),
                "address_components": result.get("address_components", [])
            }

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": formatted_result
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

