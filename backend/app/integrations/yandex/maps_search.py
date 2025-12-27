"""Yandex Maps Search integration using direct HTTP requests to Yandex Maps API."""
from typing import Dict, Any, Optional, List
from uuid import UUID
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class YandexMapsSearchIntegration(BaseIntegration):
    """Integration for searching locations using Yandex Maps API."""
    
    API_URL = "https://search-maps.yandex.ru/v1/"
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_maps_search",
            version="1.0.0",
            name="Yandex Maps Search",
            description="Поиск мест и организаций на карте через Yandex Maps API",
            category="maps",
            icon_s3_key="icons/integrations/yandex_maps.svg",
            color="#FF0000",
            config_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "title": "Search Query",
                        "description": "Поисковый запрос (например: 'кафе', 'аптека', 'метро')"
                    },
                    "lat": {
                        "type": "number",
                        "title": "Latitude",
                        "description": "Широта центра поиска (например: 55.751244)",
                        "default": None
                    },
                    "lon": {
                        "type": "number",
                        "title": "Longitude",
                        "description": "Долгота центра поиска (например: 37.618423)",
                        "default": None
                    },
                    "radius": {
                        "type": "integer",
                        "title": "Search Radius (meters)",
                        "description": "Радиус поиска в метрах (макс. 50000)",
                        "minimum": 1,
                        "maximum": 50000,
                        "default": 1000
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык ответа (ru_RU, en_US, uk_UA, tr_TR)",
                        "enum": ["ru_RU", "en_US", "uk_UA", "tr_TR"],
                        "default": "ru_RU"
                    },
                    "results": {
                        "type": "integer",
                        "title": "Max Results",
                        "description": "Максимальное количество результатов (1-500)",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 10
                    },
                    "type": {
                        "type": "string",
                        "title": "Result Type",
                        "description": "Тип искомых объектов (необязательно)",
                        "enum": ["biz", "geo", "transit"],
                        "default": "biz"
                    }
                }
            },
            credentials_provider="yandex_maps",
            credentials_strategy="api_key",
            library_name=None,  # Using direct HTTP requests with httpx
            examples=[
                {
                    "title": "Поиск кафе рядом",
                    "config": {
                        "query": "кафе",
                        "lat": 55.751244,
                        "lon": 37.618423,
                        "radius": 1000,
                        "results": 5
                    }
                },
                {
                    "title": "Поиск аптек",
                    "config": {
                        "query": "аптека",
                        "lat": 55.751244,
                        "lon": 37.618423,
                        "radius": 2000,
                        "type": "biz"
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
        Выполняет поиск мест через Yandex Maps API.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате:
            {
                "response": {
                    "ok": bool,
                    "result": dict | None,
                    "error": str | None,
                    "error_code": int | None
                }
            }
        """
        try:
            # Получаем API ключ из credentials
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="yandex_maps"
            )
            
            if not creds or not creds.api_key:
                error_msg = "Yandex Maps API key is not configured"
                await logger.error(error_msg)
                return {
                    "response": {
                        "ok": False,
                        "error": error_msg,
                        "error_code": 401
                    }
                }
            
            # Подготавливаем параметры запроса
            params = {
                "apikey": creds.api_key,
                "text": config["query"],
                "lang": config.get("lang", "ru_RU"),
                "results": min(500, max(1, config.get("results", 10))),
                "type": config.get("type", "biz")
            }
            
            # Добавляем координаты, если они указаны
            if "lat" in config and "lon" in config:
                params["ll"] = f"{config['lon']},{config['lat']}"
                params["spn"] = f"{config.get('radius', 1000) / 100000:.6f},{config.get('radius', 1000) / 100000:.6f}"
            
            # Отправляем запрос к API
            async with httpx.AsyncClient() as client:
                response = await client.get(self.API_URL, params=params, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                
                # Обрабатываем успешный ответ
                if "features" in result:
                    return {
                        "response": {
                            "ok": True,
                            "result": result
                        }
                    }
                else:
                    error_msg = result.get("message", "No results found")
                    await logger.warning(f"Yandex Maps API error: {error_msg}")
                    return {
                        "response": {
                            "ok": False,
                            "error": error_msg,
                            "error_code": 404
                        }
                    }
                    
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {str(e)}"
            await logger.error(error_msg)
            return {
                "response": {
                    "ok": False,
                    "error": error_msg,
                    "error_code": e.response.status_code if hasattr(e, 'response') else 500
                }
            }
            
        except Exception as e:
            error_msg = f"Error in Yandex Maps search: {str(e)}"
            await logger.error(error_msg)
            return {
                "response": {
                    "ok": False,
                    "error": error_msg,
                    "error_code": 500
                }
            }
