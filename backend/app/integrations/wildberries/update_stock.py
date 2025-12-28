"""Wildberries Update Stock интеграция используя httpx библиотеку."""
from typing import Dict, Any, List
from uuid import UUID
import json
from datetime import datetime

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку httpx напрямую для HTTP запросов
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class WildberriesUpdateStockIntegration(BaseIntegration):
    """
    ИНТЕГРАЦИЯ: WildberriesUpdateStockIntegration
    
    Назначение: Обновление остатков товаров на маркетплейсе Wildberries
    Эндпоинт: POST /api/v2/stocks (Marketplace API v2)
    Документация: https://openapi.wildberries.ru/marketplace/api/ru/#tag/Ostatki/paths/~1api~1v2~1stocks/post
    """
    
    @property
    def metadata(self) -> IntegrationMetadata:
        """
        МЕТАДАННЫЕ ИНТЕГРАЦИИ ДЛЯ ОБНОВЛЕНИЯ ОСТАТКОВ WILDBERRIES API v2
        """
        return IntegrationMetadata(
            # Базовые идентификаторы
            id="wildberries_update_stock",
            version="2.0.0",  # Обновили версию для API v2
            name="Wildberries Update Stock",
            description="Обновление остатков товаров на маркетплейсе Wildberries (API v2)",
            
            # Категоризация
            category="ecommerce",
            icon_s3_key="icons/integrations/wildberries.svg",
            color="#ff3100",  # Цвет Wildberries
            
            # СХЕМА КОНФИГУРАЦИИ для API v2
            config_schema={
                "type": "object",
                "required": ["stocks"],
                "properties": {
                    "stocks": {
                        "type": "array",
                        "title": "Список остатков",
                        "description": "Список объектов с данными об остатках товаров для API v2",
                        "items": {
                            "type": "object",
                            "required": ["barcode", "stock"],
                            "properties": {
                                "barcode": {
                                    "type": "string",
                                    "title": "Баркод/SKU товара",
                                    "description": "Штрихкод или артикул товара (например, '2001234567890')"
                                },
                                "stock": {
                                    "type": "integer",
                                    "title": "Количество",
                                    "description": "Количество доступных единиц товара",
                                    "minimum": 0
                                },
                                "warehouse_id": {
                                    "type": "integer",
                                    "title": "ID склада",
                                    "description": "Идентификатор склада поставщика (опционально, используется в некоторых API)"
                                }
                            }
                        },
                        "minItems": 1
                    },
                    "api_base": {
                        "type": "string",
                        "title": "База API",
                        "description": "Выбор API для использования",
                        "enum": ["marketplace", "content", "supplier"],
                        "default": "marketplace"
                    },
                    "chunk_size": {
                        "type": "integer",
                        "title": "Размер чанка",
                        "description": "Количество товаров в одном запросе (1-1000)",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 100
                    }
                }
            },
            
            # НАСТРОЙКИ АВТОРИЗАЦИИ
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            
            # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ для API v2
            examples=[
                {
                    "title": "Обновление остатка для одного товара",
                    "config": {
                        "api_base": "marketplace",
                        "stocks": [
                            {
                                "barcode": "ART1234567890",
                                "stock": 50
                            }
                        ]
                    },
                    "description": "Обновление остатка для товара до 50 единиц через Marketplace API"
                },
                {
                    "title": "Обновление остатков для нескольких товаров",
                    "config": {
                        "api_base": "marketplace",
                        "chunk_size": 50,
                        "stocks": [
                            {"barcode": "ART001", "stock": 25},
                            {"barcode": "ART002", "stock": 40},
                            {"barcode": "ART003", "stock": 15},
                            {"barcode": "ART004", "stock": 0}
                        ]
                    },
                    "description": "Обновление остатков для нескольких товаров чанками по 50"
                },
                {
                    "title": "Обнуление остатков через Content API",
                    "config": {
                        "api_base": "content",
                        "stocks": [
                            {
                                "barcode": "ART1234567890",
                                "stock": 0
                            }
                        ]
                    },
                    "description": "Обнуление остатков товара через Content API"
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
        ГЛАВНЫЙ МЕТОД ДЛЯ ОБНОВЛЕНИЯ ОСТАТКОВ WILDBERRIES API v2
        
        Особенности API v2:
        1. Использует Marketplace API v2
        2. Формат данных: {"skus": ["ART123"], "amount": 10}
        3. Авторизация: простой токен без "Bearer"
        """
        
        # ========== ШАГ 1: ПРОВЕРКА БИБЛИОТЕКИ ==========
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }
        
        # ========== ШАГ 2: ПОЛУЧЕНИЕ API КЛЮЧА ==========
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("Wildberries credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Wildberries API key not found in credentials"
                }
            }
        
        # Извлекаем payload с API ключом
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        # Ищем API ключ Wildberries
        api_key = (
            payload.get("api_key") or 
            payload.get("key") or 
            payload.get("token") or 
            payload.get("wildberries_api_key") or
            payload.get("marketplace_api_key") or
            payload.get("statistics_api_key")
        )
        
        if not api_key:
            await logger.error(f"API key not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "API key not found in credentials"
                }
            }
        
        # ========== ШАГ 3: ПОЛУЧЕНИЕ И ВАЛИДАЦИЯ ПАРАМЕТРОВ ==========
        stocks = config.get("stocks", [])
        api_base = config.get("api_base", "marketplace")
        chunk_size = min(max(config.get("chunk_size", 100), 1), 1000)  # Ограничение 1-1000
        
        if not stocks:
            await logger.error("stocks parameter is required and cannot be empty")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "stocks parameter is required and cannot be empty"
                }
            }
        
        if not isinstance(stocks, list):
            await logger.error("stocks must be a list")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "stocks must be a list"
                }
            }
        
        # Валидация каждого элемента stocks
        validated_stocks = []
        for i, stock_item in enumerate(stocks):
            if not isinstance(stock_item, dict):
                await logger.error(f"stock item at index {i} must be an object")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"stock item at index {i} must be an object"
                    }
                }
            
            barcode = stock_item.get("barcode")
            stock = stock_item.get("stock")
            
            if not barcode or not isinstance(barcode, str) or not barcode.strip():
                await logger.error(f"barcode at index {i} must be a non-empty string")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"barcode at index {i} must be a non-empty string"
                    }
                }
            
            if stock is None or not isinstance(stock, int) or stock < 0:
                await logger.error(f"stock at index {i} must be a non-negative integer")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": f"stock at index {i} must be a non-negative integer"
                    }
                }
            
            # Подготавливаем валидированный объект
            validated_item = {
                "barcode": str(barcode).strip(),
                "stock": stock
            }
            
            # warehouse_id может понадобиться для других API
            warehouse_id = stock_item.get("warehouse_id")
            if warehouse_id is not None:
                if isinstance(warehouse_id, int) and warehouse_id > 0:
                    validated_item["warehouse_id"] = warehouse_id
                else:
                    await logger.warning(f"Invalid warehouse_id at index {i}, ignoring")
            
            validated_stocks.append(validated_item)
        
        await logger.info(f"Validated {len(validated_stocks)} stock items for update")
        
        # ========== ШАГ 4: ПОДГОТОВКА ДАННЫХ ДЛЯ API v2 ==========
        def prepare_wb_v2_stocks(stock_items: List[Dict]) -> List[Dict]:
            """Преобразование данных в формат WB API v2"""
            wb_stocks = []
            for item in stock_items:
                wb_stocks.append({
                    "skus": [item["barcode"]],  # ОБЯЗАТЕЛЬНО массив!
                    "amount": item["stock"]      # Поле называется amount в API v2!
                })
            return wb_stocks
        
        # Разбиваем на чанки для избежания лимитов
        chunks = [
            validated_stocks[i:i + chunk_size] 
            for i in range(0, len(validated_stocks), chunk_size)
        ]
        
        await logger.info(f"Split into {len(chunks)} chunks of max {chunk_size} items each")
        
        # ========== ШАГ 5: ВЫПОЛНЕНИЕ HTTP ЗАПРОСОВ ==========
        """
        Ключевой запрос к Wildberries API v2 для обновления остатков
        Формат данных: [{"skus": ["ART123"], "amount": 10}]
        Авторизация: простой токен без "Bearer"
        """
        
        # Выбираем URL в зависимости от выбранного API
        api_urls = {
            "marketplace": "https://marketplace-api.wildberries.ru/api/v2/stocks",
            "content": "https://content-api.wildberries.ru/api/v2/stocks",
            "supplier": "https://supplier-api.wildberries.ru/api/v2/stocks"
        }
        
        url = api_urls.get(api_base, api_urls["marketplace"])
        
        await logger.info(f"Using {api_base} API: {url}")
        
        # Заголовки запроса (ВАЖНО: без "Bearer"!)
        headers = {
            "Authorization": str(api_key).strip(),  # БЕЗ "Bearer"!
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "DBCV-Integration/2.0"
        }
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "api_used": api_base,
            "url": url,
            "total_items": len(validated_stocks),
            "chunks_sent": len(chunks),
            "chunks": [],
            "summary": {
                "successful": 0,
                "failed": 0,
                "total_processed": 0
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for chunk_index, chunk in enumerate(chunks):
                    # Подготавливаем данные для этого чанка
                    wb_stocks_data = prepare_wb_v2_stocks(chunk)
                    
                    chunk_result = {
                        "chunk_index": chunk_index,
                        "items_in_chunk": len(chunk),
                        "status": "pending",
                        "response": None,
                        "error": None
                    }
                    
                    try:
                        # Асинхронный HTTP POST запрос
                        response = await client.post(
                            url,
                            json=wb_stocks_data,  # API v2 формат
                            headers=headers
                        )
                        
                        chunk_result["response_status"] = response.status_code
                        
                        if response.status_code == 200:
                            # УСПЕХ: Остатки успешно обновлены
                            response_data = response.json()
                            chunk_result["status"] = "success"
                            chunk_result["response"] = response_data
                            chunk_result["items_processed"] = len(chunk)
                            
                            all_results["summary"]["successful"] += len(chunk)
                            all_results["summary"]["total_processed"] += len(chunk)
                            
                            await logger.info(f"Chunk {chunk_index + 1}/{len(chunks)}: Successfully updated {len(chunk)} items")
                            
                        elif response.status_code == 207:
                            # Multi-Status: часть успешно, часть с ошибками
                            response_data = response.json()
                            chunk_result["status"] = "partial"
                            chunk_result["response"] = response_data
                            
                            # Анализируем ответ 207
                            success_count = self._count_successful_in_207(response_data)
                            failed_count = len(chunk) - success_count
                            
                            chunk_result["items_processed"] = success_count
                            chunk_result["items_failed"] = failed_count
                            
                            all_results["summary"]["successful"] += success_count
                            all_results["summary"]["failed"] += failed_count
                            all_results["summary"]["total_processed"] += len(chunk)
                            
                            await logger.warning(
                                f"Chunk {chunk_index + 1}/{len(chunks)}: "
                                f"Partially updated {success_count}/{len(chunk)} items"
                            )
                            
                        else:
                            # Ошибка API
                            chunk_result["status"] = "error"
                            chunk_result["error"] = self._parse_wb_api_error(response)
                            
                            all_results["summary"]["failed"] += len(chunk)
                            all_results["summary"]["total_processed"] += len(chunk)
                            
                            error_msg = self._parse_wb_api_error(response)
                            await logger.error(
                                f"Chunk {chunk_index + 1}/{len(chunks)}: "
                                f"API error: {error_msg}"
                            )
                        
                    except httpx.TimeoutException as e:
                        chunk_result["status"] = "timeout"
                        chunk_result["error"] = f"Request timeout: {str(e)}"
                        all_results["summary"]["failed"] += len(chunk)
                        
                        await logger.error(f"Chunk {chunk_index + 1}/{len(chunks)}: Timeout error")
                        
                    except httpx.RequestError as e:
                        chunk_result["status"] = "request_error"
                        chunk_result["error"] = f"HTTP request error: {str(e)}"
                        all_results["summary"]["failed"] += len(chunk)
                        
                        await logger.error(f"Chunk {chunk_index + 1}/{len(chunks)}: Request error: {e}")
                    
                    all_results["chunks"].append(chunk_result)
                    
                    # Небольшая пауза между чанками для избежания rate limiting
                    if chunk_index < len(chunks) - 1:
                        await asyncio.sleep(0.5)
                
                # Форматируем финальный результат
                formatted_result = self._format_response(all_results)
                
                # Логируем итоги
                success_rate = (
                    (all_results["summary"]["successful"] / all_results["total_items"] * 100)
                    if all_results["total_items"] > 0 else 0
                )
                
                await logger.info(
                    f"Stock update completed: "
                    f"{all_results['summary']['successful']}/{all_results['total_items']} "
                    f"items ({success_rate:.1f}%) successful"
                )
                
                # Возвращаем результат
                return {
                    "response": {
                        "ok": True,
                        "result": formatted_result
                    }
                }
                    
        except Exception as e:
            await logger.error(f"Unexpected error in stock update: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}",
                    "partial_result": all_results if all_results["chunks"] else None
                }
            }
    
    def _count_successful_in_207(self, response_data: Dict) -> int:
        """Подсчет успешных обновлений в ответе 207 Multi-Status"""
        if not isinstance(response_data, dict):
            return 0
        
        # Формат ответа 207 может варьироваться
        # Ищем массивы с результатами
        success_count = 0
        
        if "stocks" in response_data and isinstance(response_data["stocks"], list):
            # Формат: {"stocks": [{"sku": "...", "amount": ..., "updated": true/false}]}
            for item in response_data["stocks"]:
                if isinstance(item, dict) and item.get("updated") is True:
                    success_count += 1
        
        elif isinstance(response_data, list):
            # Формат: [{"sku": "...", "amount": ..., "updated": true/false}]
            for item in response_data:
                if isinstance(item, dict) and item.get("updated") is True:
                    success_count += 1
        
        return success_count
    
    def _format_response(self, all_results: Dict) -> Dict[str, Any]:
        """Форматирование финального результата"""
        return {
            "execution_summary": {
                "timestamp": all_results["timestamp"],
                "api_used": all_results["api_used"],
                "total_items": all_results["total_items"],
                "chunks_sent": all_results["chunks_sent"]
            },
            "statistics": all_results["summary"],
            "chunks_detail": [
                {
                    "chunk": chunk["chunk_index"],
                    "status": chunk["status"],
                    "items": chunk.get("items_in_chunk", 0),
                    "processed": chunk.get("items_processed", 0),
                    "failed": chunk.get("items_failed", 0),
                    "error": chunk.get("error") if chunk["status"] in ["error", "timeout", "request_error"] else None
                }
                for chunk in all_results["chunks"]
            ],
            "success_rate_percent": (
                (all_results["summary"]["successful"] / all_results["total_items"] * 100)
                if all_results["total_items"] > 0 else 0
            )
        }
    
    def _parse_wb_api_error(self, response) -> str:
        """
        ПАРСИНГ ОШИБОК WILDBERRIES API v2
        """
        status_messages = {
            400: "Неверные параметры запроса",
            401: "Неверный или отсутствующий API ключ",
            403: "Доступ запрещен. Проверьте права API ключа",
            404: "Запрошенный ресурс не найден",
            409: "Конфликт данных (например, дублирование)",
            413: "Слишком большой запрос",
            422: "Неверный формат данных",
            429: "Превышен лимит запросов к Wildberries API",
            500: "Внутренняя ошибка сервера Wildberries",
            502: "Плохой шлюз",
            503: "Сервис временно недоступен",
            504: "Таймаут шлюза"
        }
        
        default_message = f"HTTP ошибка {response.status_code}"
        
        if response.text:
            try:
                error_data = json.loads(response.text)
                
                if isinstance(error_data, dict):
                    # Wildberries API v2 формат ошибок
                    error_fields = [
                        error_data.get("detail"),
                        error_data.get("title"),
                        error_data.get("message"),
                        error_data.get("errorText"),
                        error_data.get("error")
                    ]
                    
                    for field in error_fields:
                        if field:
                            return f"{status_messages.get(response.status_code, default_message)}: {field}"
                    
                    # Проверяем вложенные ошибки
                    if "errors" in error_data and error_data["errors"]:
                        if isinstance(error_data["errors"], list) and error_data["errors"]:
                            first_error = error_data["errors"][0]
                            if isinstance(first_error, dict):
                                error_msg = first_error.get("message") or str(first_error)
                                return f"{status_messages.get(response.status_code, default_message)}: {error_msg}"
                
                elif isinstance(error_data, str):
                    return f"{status_messages.get(response.status_code, default_message)}: {error_data}"
                    
            except json.JSONDecodeError:
                # Если не JSON, возвращаем текст
                if response.text and len(response.text) < 500:
                    return f"{status_messages.get(response.status_code, default_message)}: {response.text}"
            except Exception:
                pass
        
        return status_messages.get(response.status_code, default_message)