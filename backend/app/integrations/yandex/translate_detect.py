"""Yandex Translate Detect интеграция для определения языка текста (API v2)."""
from typing import Dict, Any, List, Optional
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


class YandexTranslateDetectIntegration(BaseIntegration):
    """Интеграция для определения языка текста через Яндекс.Переводчик (API v2)."""

    # URL для API Яндекс.Переводчика v2 - определение языка
    API_URL = "https://translate.api.cloud.yandex.net/translate/v2/detect"

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_translate_detect",
            version="2.0.0",
            name="Yandex Translate Detect",
            description="Определение языка текста через Яндекс.Переводчик (API v2)",
            category="translation",
            icon_s3_key="icons/integrations/yandex.svg",
            color="#ff0000",  # Красный цвет Яндекс
            config_schema={
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {
                        "type": "string",
                        "title": "Текст",
                        "description": "Текст, для которого нужно определить язык",
                        "minLength": 1
                    },
                    "languageCodeHints": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": "^[a-z]{2}$",
                            "examples": ["ru", "en", "de", "fr", "es"]
                        },
                        "title": "Подсказки языка",
                        "description": "Список наиболее вероятных языков (формат ISO 639-1, напр. ['ru', 'en'])"
                    },
                    "folderId": {
                        "type": "string",
                        "title": "Идентификатор каталога",
                        "description": "ID каталога в Yandex Cloud. Обязателен для аутентификации с аккаунтом пользователя."
                    }
                },
                "additionalProperties": False
            },
            credentials_provider="yandex_cloud",
            credentials_strategy="service_account",
            library_name="httpx>=0.24.0",
            examples=[
                {
                    "title": "Определить язык простого текста",
                    "config": {
                        "text": "Hello world"
                    }
                },
                {
                    "title": "Определить язык с подсказками",
                    "config": {
                        "text": "Привет, как дела?",
                        "languageCodeHints": ["ru", "uk", "be"]
                    }
                },
                {
                    "title": "Определить язык с указанием каталога",
                    "description": "Для аккаунта пользователя необходимо указать folderId",
                    "config": {
                        "text": "Bonjour tout le monde",
                        "folderId": "b1gvmob95yysaplct532",
                        "languageCodeHints": ["fr", "en"]
                    }
                },
                {
                    "title": "Определить язык длинного текста",
                    "config": {
                        "text": "This is a longer text that needs language detection. The API can handle texts up to certain length limits specified in Yandex documentation."
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
        Выполняет интеграцию для определения языка текста через Яндекс.Переводчик (API v2).

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате {"response": {"ok": True, "result": {"languageCode": "ru"}}}
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error": "httpx library is not installed. Required version: >=0.24.0"
                }
            }

        # Получаем текст из конфигурации
        text = config.get("text")
        if not text:
            await logger.error("Parameter 'text' is required")
            return {
                "response": {
                    "ok": False,
                    "error": "Parameter 'text' is required"
                }
            }

        # Проверяем длину текста
        if len(text) < 1:
            await logger.error("Text cannot be empty")
            return {
                "response": {
                    "ok": False,
                    "error": "Text cannot be empty"
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

        api_key = payload.get("api_key")
        if not api_key:
            await logger.error(f"API key not found in Yandex Cloud credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error": "API key not found in Yandex Cloud credentials. Make sure 'api_key' field exists."
                }
            }

        # Получаем опциональные параметры из config
        language_code_hints = config.get("languageCodeHints")
        folder_id = config.get("folderId")

        # Подготавливаем тело запроса
        request_body: Dict[str, Any] = {
            "text": text
        }

        # Добавляем опциональные параметры, если они указаны
        if language_code_hints and isinstance(language_code_hints, list):
            # Проверяем формат кодов языков
            valid_hints = []
            for hint in language_code_hints:
                if isinstance(hint, str) and len(hint) == 2:
                    valid_hints.append(hint.lower())
                else:
                    await logger.warning(f"Invalid language code hint format: {hint}. Expected 2-letter ISO 639-1 code.")

            if valid_hints:
                request_body["languageCodeHints"] = valid_hints

        if folder_id:
            request_body["folderId"] = folder_id

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ для запроса к API v2
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Отправляем POST запрос с API-ключом в заголовке Authorization
                response = await client.post(
                    self.API_URL,
                    json=request_body,
                    headers={
                        "Authorization": f"Api-Key {api_key}",  # Важно: "Api-Key", а не "Bearer"
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

                        # Проверяем, что ответ содержит ожидаемое поле languageCode
                        if not isinstance(result, dict) or "languageCode" not in result:
                            await logger.error(f"Unexpected API response format: {result}")
                            return {
                                "response": {
                                    "ok": False,
                                    "error": "Invalid API response format: missing 'languageCode' field"
                                }
                            }

                        language_code = result["languageCode"]

                        # Проверяем, что код языка валидный
                        if not isinstance(language_code, str) or len(language_code) != 2:
                            await logger.warning(f"API returned unexpected language code format: {language_code}")

                        # Возвращаем успешный результат в формате системы
                        return {
                            "response": {
                                "ok": True,
                                "result": {
                                    "languageCode": language_code,
                                    "detectedLanguage": language_code
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

                elif response.status_code == 400:
                    await logger.error("Yandex Translate API v2: Bad Request")
                    error_info = "Bad request"
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                        elif "error" in error_json:
                            error_info = error_json["error"]
                    except ValueError:
                        pass

                    # Проверяем специфичные ошибки
                    if "text" in error_info.lower():
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Invalid text parameter: {error_info}"
                            }
                        }
                    elif "languageCodeHints" in error_info.lower():
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Invalid languageCodeHints: {error_info}"
                            }
                        }
                    elif "folderId" in error_info.lower():
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Invalid or missing folderId: {error_info}"
                            }
                        }

                    return {
                        "response": {
                            "ok": False,
                            "error": f"Bad request: {error_info}"
                        }
                    }

                elif response.status_code == 401:
                    await logger.error("Yandex Translate API v2: Unauthorized (invalid API key)")
                    error_info = "Invalid API key"
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                    except ValueError:
                        pass

                    return {
                        "response": {
                            "ok": False,
                            "error": f"Authentication failed: {error_info}"
                        }
                    }

                elif response.status_code == 403:
                    await logger.error("Yandex Translate API v2: Forbidden")
                    error_info = "Access forbidden"
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                    except ValueError:
                        pass

                    # Проверяем, не связана ли ошибка с отсутствием folderId
                    if "folderId" in error_info or "folder" in error_info:
                        return {
                            "response": {
                                "ok": False,
                                "error": "folderId is required for user account authentication. Please specify folderId in config or use service account credentials."
                            }
                        }

                    return {
                        "response": {
                            "ok": False,
                            "error": f"Access forbidden: {error_info}. Check API key permissions and folder access."
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
                    error_info = "Rate limit exceeded"
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                    except ValueError:
                        pass

                    return {
                        "response": {
                            "ok": False,
                            "error": f"{error_info}. Try again later or increase rate limits in Yandex Cloud."
                        }
                    }

                elif 500 <= response.status_code < 600:
                    await logger.error(f"Yandex Translate API v2: Server Error ({response.status_code})")
                    error_info = "Internal server error"
                    try:
                        error_json = response.json()
                        if "message" in error_json:
                            error_info = error_json["message"]
                    except ValueError:
                        pass

                    return {
                        "response": {
                            "ok": False,
                            "error": f"Yandex Cloud server error: {error_info}"
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
                    "error": "Request to Yandex Translate API timed out after 30 seconds"
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
            await logger.error(f"Unexpected error in Yandex Translate Detect integration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": f"Unexpected error: {str(e)}"
                }
            }