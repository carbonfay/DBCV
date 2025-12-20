"""Yandex Translate Languages интеграция для получения списка поддерживаемых языков (API v2)."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx для HTTP запросов
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    # Создаем заглушку для type checking
    class httpx:
        class AsyncClient:
            def __init__(self, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def post(self, *args, **kwargs):
                pass
        
        class TimeoutException(Exception):
            pass
        
        class RequestError(Exception):
            pass


class YandexTranslateLanguagesIntegration(BaseIntegration):
    """Интеграция для получения списка поддерживаемых языков Яндекс.Переводчика (API v2)."""
    
    # URL для нового API Яндекс.Переводчика v2
    API_URL = "https://translate.api.cloud.yandex.net/translate/v2/languages"
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_translate_languages",
            version="2.0.0",  # Обновили версию из-за смены API
            name="Yandex Translate Languages",
            description="Получение списка поддерживаемых языков для перевода через Яндекс.Переводчик (API v2)",
            category="translation",
            icon_s3_key="icons/integrations/yandex.svg",
            color="#ff0000",  # Красный цвет Яндекс
            config_schema={
                "type": "object",
                "properties": {
                    "folderId": {
                        "type": "string",
                        "title": "Идентификатор каталога",
                        "description": "ID каталога в Yandex Cloud. Обязателен для аутентификации с аккаунтом пользователя."
                    }
                },
                "additionalProperties": False
            },
            credentials_provider="yandex_cloud",
            credentials_strategy="api_key",
            library_name="httpx>=0.24.0",
            examples=[
                {
                    "title": "Получить список языков (сервисный аккаунт)",
                    "description": "Для сервисного аккаунта folderId можно не указывать",
                    "config": {}
                },
                {
                    "title": "Получить список языков (аккаунт пользователя)",
                    "description": "Для аккаунта пользователя необходимо указать folderId",
                    "config": {
                        "folderId": "b1gvmob95yysaplct532"
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
        Выполняет интеграцию для получения списка поддерживаемых языков Яндекс.Переводчика (API v2).
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате {"response": {"ok": True, "result": {...}}}
        """

        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error": "httpx library is not installed. Required version: >=0.24.0"
                }
            }
        
        # Получаем credentials для Yandex Cloud
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="yandex_cloud",
            strategy="service_account"
        )
        
        if not creds:
            await logger.error("Yandex Cloud credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error": "Yandex Cloud API key not found in credentials"
                }
            }
        
        # Получаем API ключ из credentials
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        api_key = payload.get("api_key") or payload.get("key")
        if not api_key:
            await logger.error(f"API key not found in Yandex Cloud credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error": "API key not found in Yandex Cloud credentials"
                }
            }
        
        # Получаем параметр folderId из config (может быть None для сервисного аккаунта)
        folder_id = config.get("folderId")
        
        # Подготавливаем тело запроса
        request_body = {}
        if folder_id:
            request_body["folderId"] = folder_id
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ для запроса к новому API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Отправляем POST запрос с API-ключом в заголовке
                response = await client.post(
                    self.API_URL,
                    json=request_body if request_body else None,
                    headers={
                        "Authorization": f"Api-Key {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "DBCV-Integration/2.0",
                        "Accept": "application/json"
                    }
                )
                
                # Проверяем статус ответа
                if response.status_code == 200:
                    # Пытаемся распарсить JSON
                    try:
                        result = response.json()
                        
                        # Проверяем, что ответ содержит ожидаемые поля
                        if not isinstance(result, dict) or "languages" not in result:
                            await logger.error(f"Unexpected API response format: {result}")
                            return {
                                "response": {
                                    "ok": False,
                                    "error": "Invalid API response format: missing 'languages' field"
                                }
                            }
                        
                        # Форматируем результат для обратной совместимости со старым форматом
                        # Преобразуем массив объектов в словарь code->name для удобства
                        languages_dict = {}
                        for lang in result.get("languages", []):
                            if "code" in lang and "name" in lang:
                                languages_dict[lang["code"]] = lang["name"]
                        
                        # Возвращаем успешный результат в формате системы
                        return {
                            "response": {
                                "ok": True,
                                "result": {
                                    "languages": result.get("languages", []),  # Оригинальный массив
                                    "langs": languages_dict,  # Словарь для обратной совместимости
                                    "codes": list(languages_dict.keys())  # Список кодов языков
                                }
                            }
                        }
                        
                    except ValueError as e:
                        await logger.error(f"Failed to parse JSON response: {e}. Response: {response.text}")
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Failed to parse API response: {str(e)}"
                            }
                        }
                    
                elif response.status_code == 401:
                    await logger.error("Yandex Translate API v2: Unauthorized (invalid API key)")
                    return {
                        "response": {
                            "ok": False,
                            "error": "Invalid API key or insufficient permissions"
                        }
                    }
                    
                elif response.status_code == 403:
                    await logger.error("Yandex Translate API v2: Forbidden")
                    error_info = response.text
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                    except ValueError:
                        pass
                    
                    return {
                        "response": {
                            "ok": False,
                            "error": f"Access forbidden: {error_info}. Check API key permissions and folder access."
                        }
                    }
                    
                elif response.status_code == 400:
                    await logger.error("Yandex Translate API v2: Bad Request")
                    error_info = response.text
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                    except ValueError:
                        pass
                    
                    # Проверяем, не связана ли ошибка с отсутствием folderId
                    if "folderId" in error_info:
                        return {
                            "response": {
                                "ok": False,
                                "error": "folderId is required for user account authentication. Please specify folderId in config."
                            }
                        }
                    
                    return {
                        "response": {
                            "ok": False,
                            "error": f"Bad request: {error_info}"
                        }
                    }
                    
                elif response.status_code == 404:
                    await logger.error("Yandex Translate API v2: Not Found")
                    return {
                        "response": {
                            "ok": False,
                            "error": "API endpoint not found. Please check the API URL."
                        }
                    }
                    
                elif response.status_code == 429:
                    await logger.error("Yandex Translate API v2: Too Many Requests")
                    return {
                        "response": {
                            "ok": False,
                            "error": "Rate limit exceeded. Try again later"
                        }
                    }
                    
                else:
                    # Пытаемся получить информацию об ошибке из ответа
                    error_info = response.text
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                        elif "error" in error_json:
                            error_info = error_json["error"]
                    except ValueError:
                        pass
                    
                    await logger.error(f"Yandex Translate API v2 error {response.status_code}: {error_info}")
                    return {
                        "response": {
                            "ok": False,
                            "error": f"API error {response.status_code}: {error_info}"
                        }
                    }
                    
        except httpx.TimeoutException:
            await logger.error("Request to Yandex Translate API v2 timed out")
            return {
                "response": {
                    "ok": False,
                    "error": "Request to Yandex Translate API timed out"
                }
            }
            
        except httpx.RequestError as e:
            await logger.error(f"Network error while connecting to Yandex Translate API v2: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": f"Network error: {str(e)}"
                }
            }
            
        except Exception as e:
            await logger.error(f"Unexpected error in Yandex Translate Languages integration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": f"Unexpected error: {str(e)}"
                }
            }