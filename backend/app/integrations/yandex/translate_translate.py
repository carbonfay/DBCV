"""Yandex Translate Translate интеграция для перевода текста (API v2)."""
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


class YandexTranslateTranslateIntegration(BaseIntegration):
    """Интеграция для перевода текста через Яндекс.Переводчик (API v2)."""

    # URL для API Яндекс.Переводчика v2 - перевод текста
    API_URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"

    # Максимальная суммарная длина текстов (символов)
    MAX_TEXTS_LENGTH = 10000

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yandex_translate_translate",
            version="2.0.0",
            name="Yandex Translate Translate",
            description="Перевод текста через Яндекс.Переводчик (API v2)",
            category="translation",
            icon_s3_key="icons/integrations/yandex.svg",
            color="#ff0000",  # Красный цвет Яндекс
            config_schema={
                "type": "object",
                "required": ["targetLanguageCode", "texts"],
                "properties": {
                    "sourceLanguageCode": {
                        "type": "string",
                        "title": "Исходный язык",
                        "description": "Язык исходного текста (например, 'ru'). Определяется автоматически, если не указан.",
                        "pattern": "^[a-z]{2}$",
                        "examples": ["ru", "en", "de", "fr", "es"]
                    },
                    "targetLanguageCode": {
                        "type": "string",
                        "title": "Целевой язык",
                        "description": "Обязательное поле. Язык, на который нужно перевести (например, 'en').",
                        "pattern": "^[a-z]{2}$",
                        "examples": ["en", "ru", "de", "fr", "es"]
                    },
                    "format": {
                        "type": "string",
                        "title": "Формат текста",
                        "description": "Формат текста. По умолчанию 'PLAIN_TEXT'.",
                        "enum": ["PLAIN_TEXT", "HTML"],
                        "default": "PLAIN_TEXT"
                    },
                    "texts": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "minLength": 1
                        },
                        "title": "Тексты для перевода",
                        "description": "Обязательное поле. Массив текстов для перевода (максимум 10000 символов суммарно)."
                    },
                    "folderId": {
                        "type": "string",
                        "title": "Идентификатор каталога",
                        "description": "ID каталога в Yandex Cloud. Обязателен для аутентификации с аккаунтом пользователя."
                    },
                    "model": {
                        "type": "string",
                        "title": "ID модели",
                        "description": "Идентификатор кастомной модели перевода."
                    },
                    "speller": {
                        "type": "boolean",
                        "title": "Проверка орфографии",
                        "description": "Включить проверку орфографии для исходного текста.",
                        "default": False
                    }
                },
                "additionalProperties": False
            },
            credentials_provider="yandex_cloud",
            credentials_strategy="service_account",
            library_name="httpx>=0.24.0",
            examples=[
                {
                    "title": "Перевести текст с русского на английский",
                    "config": {
                        "sourceLanguageCode": "ru",
                        "targetLanguageCode": "en",
                        "texts": ["Привет, мир!", "Как дела?"]
                    }
                },
                {
                    "title": "Перевести текст с автоопределением языка",
                    "config": {
                        "targetLanguageCode": "ru",
                        "texts": ["Hello world", "Good morning"]
                    }
                },
                {
                    "title": "Перевести HTML текст",
                    "config": {
                        "targetLanguageCode": "en",
                        "texts": ["<h1>Заголовок</h1><p>Абзац текста</p>"],
                        "format": "HTML"
                    }
                },
                {
                    "title": "Перевести с проверкой орфографии",
                    "config": {
                        "sourceLanguageCode": "ru",
                        "targetLanguageCode": "en",
                        "texts": ["Привет, как дила?"],  # Опечатка специально
                        "speller": True
                    }
                },
                {
                    "title": "Перевести с указанием каталога",
                    "description": "Для аккаунта пользователя необходимо указать folderId",
                    "config": {
                        "targetLanguageCode": "en",
                        "texts": ["Bonjour tout le monde"],
                        "folderId": "b1gvmob95yysaplct532"
                    }
                },
                {
                    "title": "Перевести несколько текстов одновременно",
                    "config": {
                        "sourceLanguageCode": "en",
                        "targetLanguageCode": "ru",
                        "texts": [
                            "Hello, how are you?",
                            "Thank you very much",
                            "I would like to order a coffee"
                        ]
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
        Выполняет интеграцию для перевода текста через Яндекс.Переводчик (API v2).

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

        # Получаем обязательные параметры из конфигурации
        target_language = config.get("targetLanguageCode")
        texts = config.get("texts")

        # Валидация обязательных параметров
        if not target_language:
            await logger.error("Parameter 'targetLanguageCode' is required")
            return {
                "response": {
                    "ok": False,
                    "error": "Parameter 'targetLanguageCode' is required"
                }
            }

        if not texts or not isinstance(texts, list):
            await logger.error("Parameter 'texts' is required and must be an array")
            return {
                "response": {
                    "ok": False,
                    "error": "Parameter 'texts' is required and must be an array of strings"
                }
            }

        if len(texts) == 0:
            await logger.error("Parameter 'texts' must contain at least one text")
            return {
                "response": {
                    "ok": False,
                    "error": "Parameter 'texts' must contain at least one text"
                }
            }

        # Проверяем, что все элементы массива - строки
        valid_texts = []
        total_length = 0

        for i, text in enumerate(texts):
            if not isinstance(text, str):
                await logger.error(f"Text at index {i} is not a string: {type(text)}")
                return {
                    "response": {
                        "ok": False,
                        "error": f"Text at index {i} is not a string"
                    }
                }

            if len(text) == 0:
                await logger.error(f"Text at index {i} is empty")
                return {
                    "response": {
                        "ok": False,
                        "error": f"Text at index {i} is empty"
                    }
                }

            valid_texts.append(text)
            total_length += len(text)

        # Проверяем суммарную длину текстов
        if total_length > self.MAX_TEXTS_LENGTH:
            await logger.error(f"Total texts length ({total_length}) exceeds maximum ({self.MAX_TEXTS_LENGTH})")
            return {
                "response": {
                    "ok": False,
                    "error": f"Total texts length ({total_length} characters) exceeds maximum limit of {self.MAX_TEXTS_LENGTH} characters"
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
        source_language = config.get("sourceLanguageCode")
        text_format = config.get("format", "PLAIN_TEXT")
        folder_id = config.get("folderId")
        model_id = config.get("model")
        speller_enabled = config.get("speller", False)

        # Подготавливаем тело запроса
        request_body: Dict[str, Any] = {
            "targetLanguageCode": target_language,
            "texts": valid_texts,
            "format": text_format
        }

        # Добавляем опциональные параметры, если они указаны
        if source_language:
            request_body["sourceLanguageCode"] = source_language

        if folder_id:
            request_body["folderId"] = folder_id

        if model_id:
            request_body["model"] = model_id

        if speller_enabled is not None:
            request_body["speller"] = bool(speller_enabled)

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

                        # Проверяем, что ответ содержит ожидаемое поле translations
                        if not isinstance(result, dict) or "translations" not in result:
                            await logger.error(f"Unexpected API response format: {result}")
                            return {
                                "response": {
                                    "ok": False,
                                    "error": "Invalid API response format: missing 'translations' field"
                                }
                            }

                        translations = result["translations"]

                        # Проверяем, что translations - массив
                        if not isinstance(translations, list):
                            await logger.error(f"Translations field is not an array: {translations}")
                            return {
                                "response": {
                                    "ok": False,
                                    "error": "Invalid API response format: 'translations' must be an array"
                                }
                            }

                        # Возвращаем успешный результат в формате системы
                        return {
                            "response": {
                                "ok": True,
                                "result": {
                                    "translations": translations,
                                    "count": len(translations),
                                    "targetLanguage": target_language,
                                    "sourceLanguage": source_language or "auto"
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
                    error_lower = error_info.lower()

                    if "texts" in error_lower:
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Invalid texts parameter: {error_info}"
                            }
                        }
                    elif "targetlanguagecode" in error_lower or "target language" in error_lower:
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Invalid targetLanguageCode: {error_info}"
                            }
                        }
                    elif "sourcelanguagecode" in error_lower or "source language" in error_lower:
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Invalid sourceLanguageCode: {error_info}"
                            }
                        }
                    elif "format" in error_lower:
                        return {
                            "response": {
                                "ok": False,
                                "error": f"Invalid format: {error_info}"
                            }
                        }
                    elif "folderid" in error_lower:
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
                    if "folderid" in error_info.lower() or "folder" in error_info.lower():
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

                elif response.status_code == 413:
                    await logger.error("Yandex Translate API v2: Request Entity Too Large")
                    return {
                        "response": {
                            "ok": False,
                            "error": "Texts too long. Reduce the total length of texts or split into multiple requests."
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
            await logger.error(f"Unexpected error in Yandex Translate Translate integration: {e}")
            return {
                "response": {
                    "ok": False,
                    "error": f"Unexpected error: {str(e)}"
                }
            }