"""Yandex Maps Suggest интеграция для подсказок адресов."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Используем httpx для прямых HTTP запросов к Yandex Maps API
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class YandexMapsSuggestIntegration(BaseIntegration):
    """Интеграция для получения подсказок адресов через Yandex Maps Suggest API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_maps_suggest",
            version="1.0.0",
            name="Yandex Maps Suggest",
            description="Получение подсказок адресов и мест через Yandex Maps Suggest API",
            category="maps",
            icon_s3_key="icons/integrations/yandex_maps.svg",
            color="#FF0000",
            config_schema={
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {
                        "type": "string",
                        "title": "Search Text",
                        "description": "Текст для поиска (адрес, название места)"
                    },
                    "lang": {
                        "type": "string",
                        "title": "Language",
                        "description": "Язык ответа",
                        "enum": ["ru_RU", "en_US", "tr_TR", "uk_UA"],
                        "default": "ru_RU"
                    },
                    "results": {
                        "type": "integer",
                        "title": "Results Limit",
                        "description": "Количество результатов (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    },
                    "bbox": {
                        "type": "string",
                        "title": "Bounding Box",
                        "description": "Ограничивающий прямоугольник (lon1,lat1~lon2,lat2), например: 37.48,55.57~37.78,55.88"
                    },
                    "ll": {
                        "type": "string",
                        "title": "Center Point",
                        "description": "Центр области поиска (lon,lat), например: 37.618920,55.756994"
                    },
                    "spn": {
                        "type": "string",
                        "title": "Span",
                        "description": "Размер области поиска (lon_span,lat_span), например: 0.3,0.3"
                    },
                    "strict_bounds": {
                        "type": "boolean",
                        "title": "Strict Bounds",
                        "description": "Строгое ограничение области поиска",
                        "default": False
                    },
                    "types": {
                        "type": "string",
                        "title": "Result Types",
                        "description": "Типы объектов (biz - организации, geo - топонимы, transit - остановки)",
                        "enum": ["biz", "geo", "transit", "biz,geo", "biz,transit", "geo,transit", "biz,geo,transit"]
                    }
                }
            },
            credentials_provider="yandex_maps",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Поиск адреса в Москве",
                    "config": {
                        "text": "Тверская улица",
                        "lang": "ru_RU",
                        "results": 5,
                        "ll": "37.618920,55.756994",
                        "spn": "0.3,0.3"
                    }
                },
                {
                    "title": "Поиск организации",
                    "config": {
                        "text": "кафе",
                        "lang": "ru_RU",
                        "results": 3,
                        "types": "biz",
                        "ll": "37.618920,55.756994"
                    }
                },
                {
                    "title": "Строгий поиск в области",
                    "config": {
                        "text": "парк",
                        "bbox": "37.48,55.57~37.78,55.88",
                        "strict_bounds": True,
                        "results": 5
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
        Выполняет запрос к Yandex Maps Suggest API через httpx.
        
        API документация: https://yandex.ru/dev/maps/jsapi/doc/2.1/ref/reference/suggest.html
        
        Args:
            config: Параметры поиска
            credentials_resolver: Резолвер для получения API ключа
            bot_id: ID бота
            logger: Логгер
        
        Returns:
            Результат с подсказками адресов
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }
        
        # Получаем API ключ из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="yandex_maps",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Yandex Maps API key not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Yandex Maps API key not found in credentials"
                }
            }
        
        # Получаем API ключ из credentials
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("apikey")
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
        text = config.get("text")
        if not text:
            await logger.error("text parameter is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "text parameter is required"
                }
            }
        
        # Формируем параметры запроса
        params = {
            "apikey": api_key,
            "text": text,
            "lang": config.get("lang", "ru_RU"),
            "results": config.get("results", 5)
        }
        
        # Добавляем опциональные параметры
        if config.get("bbox"):
            params["bbox"] = config["bbox"]
        
        if config.get("ll"):
            params["ll"] = config["ll"]
        
        if config.get("spn"):
            params["spn"] = config["spn"]
        
        if config.get("strict_bounds"):
            params["strict_bounds"] = 1
        
        if config.get("types"):
            params["types"] = config["types"]
        
        # Выполняем запрос к Yandex Maps Suggest API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://suggest-maps.yandex.ru/v1/suggest",
                    params=params,
                    timeout=10.0
                )
                
                # Проверяем статус ответа
                if response.status_code != 200:
                    await logger.error(f"Yandex Maps API error: {response.status_code} - {response.text}")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": f"Yandex Maps API error: {response.text}"
                        }
                    }
                
                # Парсим JSON ответ
                data = response.json()
                
                # Проверяем наличие результатов
                results = data.get("results", [])
                
                # Форматируем результаты
                formatted_results = []
                for result in results:
                    formatted_result = {
                        "title": result.get("title", {}).get("text", ""),
                        "subtitle": result.get("subtitle", {}).get("text", ""),
                        "type": result.get("tags", []),
                        "distance": result.get("distance", {}).get("text", ""),
                        "uri": result.get("uri", "")
                    }
                    formatted_results.append(formatted_result)
                
                await logger.info(f"Yandex Maps Suggest: found {len(formatted_results)} results for '{text}'")
                
                # Возвращаем результат в формате системы
                return {
                    "response": {
                        "ok": True,
                        "result": {
                            "query": text,
                            "total_results": len(formatted_results),
                            "results": formatted_results
                        }
                    }
                }
        
        except httpx.TimeoutException as e:
            await logger.error(f"Yandex Maps API timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 408,
                    "description": "Request timeout"
                }
            }
        except httpx.HTTPError as e:
            await logger.error(f"HTTP error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP error: {str(e)}"
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