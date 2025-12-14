"""Telegram Send Poll интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class TelegramSendPollIntegration(BaseIntegration):
    """Интеграция для отправки опросов в Telegram через Bot API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_poll",
            version="1.0.0",
            name="Telegram Send Poll",
            description="Отправка опросов в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "question", "options"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "question": {
                        "type": "string",
                        "title": "Question",
                        "description": "Вопрос опроса"
                    },
                    "options": {
                        "type": "array",
                        "title": "Options",
                        "description": "Варианты ответов в опросе",
                        "items": {
                            "type": "string",
                            "title": "Option",
                            "description": "Вариант ответа"
                        },
                        "minItems": 2,
                        "maxItems": 10
                    },
                    "is_anonymous": {
                        "type": "boolean",
                        "title": "Is Anonymous",
                        "description": "Анонимный опрос",
                        "default": True
                    },
                    "type": {
                        "type": "string",
                        "title": "Type",
                        "description": "Тип опроса",
                        "enum": ["regular", "quiz"],
                        "default": "regular"
                    },
                    "allows_multiple_answers": {
                        "type": "boolean",
                        "title": "Allows Multiple Answers",
                        "description": "Разрешить выбор нескольких вариантов",
                        "default": False
                    },
                    "correct_option_id": {
                        "type": "integer",
                        "title": "Correct Option ID",
                        "description": "ID правильного ответа (для типа 'quiz')"
                    },
                    "explanation": {
                        "type": "string",
                        "title": "Explanation",
                        "description": "Объяснение правильного ответа (для типа 'quiz')"
                    },
                    "explanation_parse_mode": {
                        "type": "string",
                        "title": "Explanation Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "description": "Форматирование объяснения"
                    },
                    "open_period": {
                        "type": "integer",
                        "title": "Open Period",
                        "description": "Время жизни опроса в секундах"
                    },
                    "close_date": {
                        "type": "integer",
                        "title": "Close Date",
                        "description": "Время закрытия опроса в Unix timestamp"
                    },
                    "is_closed": {
                        "type": "boolean",
                        "title": "Is Closed",
                        "description": "Закрыть опрос сразу после отправки",
                        "default": False
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Простой опрос",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "question": "Какой ваш любимый язык программирования?",
                        "options": [
                            "Python",
                            "JavaScript",
                            "Java",
                            "C++"
                        ],
                        "is_anonymous": True
                    }
                },
                {
                    "title": "Викторина с правильным ответом",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "question": "Какая столица Франции?",
                        "options": [
                            "Лондон",
                            "Берлин",
                            "Париж",
                            "Мадрид"
                        ],
                        "type": "quiz",
                        "correct_option_id": 2,
                        "explanation": "Париж - столица Франции"
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
        Выполняет интеграцию используя библиотеку python-telegram-bot.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not TELEGRAM_BOT_AVAILABLE:
            await logger.error("python-telegram-bot library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "python-telegram-bot library is not installed"
                }
            }

        # Получаем bot_token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Telegram credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram bot_token not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error(f"bot_token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "bot_token not found in credentials"
                }
            }

        # Получаем параметры из config
        chat_id = config.get("chat_id")
        question = config.get("question")
        options = config.get("options")
        is_anonymous = config.get("is_anonymous", True)
        poll_type = config.get("type", "regular")
        allows_multiple_answers = config.get("allows_multiple_answers", False)
        correct_option_id = config.get("correct_option_id")
        explanation = config.get("explanation")
        explanation_parse_mode = config.get("explanation_parse_mode")
        open_period = config.get("open_period")
        close_date = config.get("close_date")
        is_closed = config.get("is_closed", False)

        if not chat_id or not question or not options or len(options) < 2:
            await logger.error("chat_id, question and at least 2 options are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id, question and at least 2 options are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            
            # Подготовим параметры для отправки опроса
            poll_kwargs = {
                "chat_id": str(chat_id),
                "question": str(question),
                "options": [str(option) for option in options],
                "is_anonymous": is_anonymous,
                "type": poll_type,
                "allows_multiple_answers": allows_multiple_answers
            }
            
            # Добавим дополнительные параметры, если они заданы
            if correct_option_id is not None:
                poll_kwargs["correct_option_id"] = int(correct_option_id)
            if explanation:
                poll_kwargs["explanation"] = str(explanation)
            if explanation_parse_mode:
                poll_kwargs["explanation_parse_mode"] = str(explanation_parse_mode)
            if open_period:
                poll_kwargs["open_period"] = int(open_period)
            if close_date:
                poll_kwargs["close_date"] = int(close_date)
            if is_closed:
                poll_kwargs["is_closed"] = bool(is_closed)

            # Отправляем опрос
            result = await bot.send_poll(**poll_kwargs)

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "message_id": result.message_id,
                        "chat": {
                            "id": result.chat.id,
                            "type": result.chat.type
                        },
                        "poll": {
                            "id": result.poll.id,
                            "question": result.poll.question,
                            "options": [
                                {
                                    "text": option.text,
                                    "voter_count": option.voter_count
                                } for option in result.poll.options
                            ],
                            "total_voter_count": result.poll.total_voter_count,
                            "is_anonymous": result.poll.is_anonymous,
                            "type": result.poll.type,
                            "allows_multiple_answers": result.poll.allows_multiple_answers,
                            "is_closed": result.poll.is_closed,
                            "is_quiz": result.poll.is_quiz
                        },
                        "date": result.date
                    }
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.error_code if hasattr(e, 'error_code') else 500,
                    "description": str(e)
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

