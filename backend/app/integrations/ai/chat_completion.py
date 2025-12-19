"""OpenAI Chat Completion интеграция используя openai библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


class OpenAIChatCompletionIntegration(BaseIntegration):
    """Интеграция для генерации ответов через OpenAI Chat Completions API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="openai_chat_completion",
            version="1.0.0",
            name="OpenAI Chat Completion",
            description="Генерация текста через OpenAI Chat Completions API",
            category="ai",
            icon_s3_key="icons/integrations/openai.svg",
            color="#10A37F",
            config_schema={
                "type": "object",
                "required": ["messages"],
                "properties": {
                    "messages": {
                        "type": "array",
                        "title": "Messages",
                        "description": "Массив сообщений для чат-комплетшена",
                        "items": {
                            "type": "object",
                            "required": ["role", "content"],
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["system", "user", "assistant"],
                                    "title": "Role",
                                    "description": "Роль отправителя"
                                },
                                "content": {
                                    "type": "string",
                                    "title": "Content",
                                    "description": "Содержание сообщения"
                                }
                            }
                        }
                    },
                    "model": {
                        "type": "string",
                        "title": "Model",
                        "description": "Модель OpenAI для использования",
                        "default": "gpt-3.5-turbo",
                        "enum": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
                    },
                    "temperature": {
                        "type": "number",
                        "title": "Temperature",
                        "description": "Случайность ответа (0.0-2.0)",
                        "default": 1.0,
                        "minimum": 0.0,
                        "maximum": 2.0
                    },
                    "max_tokens": {
                        "type": "integer",
                        "title": "Max Tokens",
                        "description": "Максимальное количество токенов в ответе",
                        "minimum": 1
                    }
                }
            },
            credentials_provider="openai",
            credentials_strategy="api_key",
            library_name="openai>=1.0.0" if OPENAI_AVAILABLE else None,
            examples=[
                {
                    "title": "Простой чат с OpenAI",
                    "config": {
                        "messages": [
                            {
                                "role": "user",
                                "content": "{$message.text$}"
                            }
                        ],
                        "model": "gpt-3.5-turbo"
                    }
                },
                {
                    "title": "Чат с системным сообщением",
                    "config": {
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful assistant."
                            },
                            {
                                "role": "user",
                                "content": "Привет, как дела?"
                            }
                        ],
                        "model": "gpt-4"
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
        Выполняет интеграцию используя библиотеку openai.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not OPENAI_AVAILABLE:
            await logger.error("openai library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "openai library is not installed"
                }
            }

        # Получаем api_key из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="openai",
            strategy="api_key"
        )

        if not creds:
            await logger.error("OpenAI credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "OpenAI api_key not found in credentials"
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
        messages = config.get("messages")
        model = config.get("model", "gpt-3.5-turbo")
        temperature = config.get("temperature", 1.0)
        max_tokens = config.get("max_tokens")

        if not messages or not isinstance(messages, list) or len(messages) == 0:
            await logger.error("messages is required and must be a non-empty list")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "messages is required and must be a non-empty list"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем клиент OpenAI
            client = openai.AsyncOpenAI(api_key=api_key)

            # Подготовим параметры для запроса
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": float(temperature),
            }

            if max_tokens:
                request_params["max_tokens"] = int(max_tokens)

            # Выполняем запрос к API
            response = await client.chat.completions.create(**request_params)

            # Извлекаем результат
            choice = response.choices[0] if response.choices else None
            message = choice.message if choice else None

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": response.id,
                        "model": response.model,
                        "created": response.created,
                        "system_fingerprint": getattr(response, 'system_fingerprint', None),
                        "choices": [
                            {
                                "index": choice.index,
                                "message": {
                                    "role": choice.message.role,
                                    "content": choice.message.content
                                },
                                "finish_reason": choice.finish_reason
                            }
                            for choice in response.choices
                        ],
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                            "total_tokens": response.usage.total_tokens if response.usage else 0
                        } if response.usage else None
                    }
                }
            }
        except openai.APIError as e:
            await logger.error(f"OpenAI API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.status_code if hasattr(e, 'status_code') else 500,
                    "description": f"OpenAI API error: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

