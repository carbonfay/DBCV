"""Интеграция для получения UV Index из OpenWeatherMap."""
from typing import Dict, Any
from uuid import UUID
import asyncio
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class GetUVIndexIntegration(BaseIntegration):
    """Интеграция для получения UV Index из OpenWeatherMap API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openweathermap_get_uv_index",
            version="1.0.0",
            name="Get UV Index",
            description="Получить индекс ультрафиолета (UV Index) для указанных координат из OpenWeatherMap",
            category="weather",
            icon_s3_key="icons/integrations/openweathermap.svg",
            color="#FF6B35",
            config_schema={
                "type": "object",
                "required": ["latitude", "longitude"],
                "properties": {
                    "latitude": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Широта (от -90 до 90)",
                        "minimum": -90,
                        "maximum": 90
                    },
                    "longitude": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Долгота (от -180 до 180)",
                        "minimum": -180,
                        "maximum": 180
                    }
                }
            },
            credentials_provider="openweathermap",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0",
            examples=[
                {
                    "title": "Получить UV Index для Москвы",
                    "config": {
                        "latitude": 55.7558,
                        "longitude": 37.6173
                    }
                },
                {
                    "title": "Получить UV Index для Санкт-Петербурга",
                    "config": {
                        "latitude": 59.9311,
                        "longitude": 30.3609
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
        Получает UV Index из OpenWeatherMap API.
        
        Args:
            config: Параметры интеграции
                - latitude: Широта (обязательно)
                - longitude: Долгота (обязательно)
            credentials_resolver: Резолвер для получения API ключа OpenWeatherMap
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        try:
            latitude = config.get("latitude")
            longitude = config.get("longitude")

            # Валидация координат
            if latitude is None or longitude is None:
                return {
                    "response": {
                        "ok": False,
                        "error": "Latitude и longitude являются обязательными параметрами"
                    }
                }

            if not (-90 <= latitude <= 90):
                return {
                    "response": {
                        "ok": False,
                        "error": "Latitude должна быть в диапазоне от -90 до 90"
                    }
                }

            if not (-180 <= longitude <= 180):
                return {
                    "response": {
                        "ok": False,
                        "error": "Longitude должна быть в диапазоне от -180 до 180"
                    }
                }

            # Получаем credentials через get_default_for (согласовано с остальными интеграциями)
            try:
                creds = await credentials_resolver.get_default_for(
                    bot_id=bot_id,
                    provider="openweathermap",
                    strategy="api_key"
                )
            except Exception as e:
                logger.error(f"Ошибка при получении credentials OpenWeatherMap: {str(e)}")
                return {
                    "response": {
                        "ok": False,
                        "error": f"Не удалось получить credentials OpenWeatherMap: {str(e)}"
                    }
                }

            if not creds:
                return {
                    "response": {
                        "ok": False,
                        "error": "API ключ OpenWeatherMap не найден. Пожалуйста, настройте credentials"
                    }
                }

            # Credentials возвращаются с ключом "payload"
            payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
            if not payload:
                payload = creds if isinstance(creds, dict) else {}

            api_key = payload.get("api_key") or payload.get("key") or payload.get("token")
            if not api_key:
                logger.error(f"api_key not found in credentials payload. Available keys: {list(payload.keys())}")
                return {
                    "response": {
                        "ok": False,
                        "error": "API ключ OpenWeatherMap не найден в credentials"
                    }
                }

            # Делаем запрос к OpenWeatherMap API используя httpx
            url = "https://api.openweathermap.org/data/2.5/uvi"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": api_key
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.error(f"OpenWeatherMap API ошибка: {response.status_code} - {response.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error": f"OpenWeatherMap API вернула ошибку {response.status_code}"
                        }
                    }

                data = response.json()

            # Обработка результата
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "uv_index": data.get("value"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "date": data.get("date"),
                        "date_iso": data.get("date_iso")
                    }
                }
            }

        except httpx.ReadTimeout:
            logger.error("Timeout при запросе к OpenWeatherMap API")
            return {
                "response": {
                    "ok": False,
                    "error": "Timeout при запросе к OpenWeatherMap API"
                }
            }
        except Exception as e:
            logger.error(f"Ошибка при получении UV Index: {str(e)}")
            return {
                "response": {
                    "ok": False,
                    "error": f"Ошибка при получении UV Index: {str(e)}"
                }
            }
