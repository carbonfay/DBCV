"""Telegram Send Message интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from telegram import Bot
    from telegram.error import TelegramError
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram import KeyboardButton, ReplyKeyboardMarkup
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    TelegramError = Exception
    InlineKeyboardButton = None
    InlineKeyboardMarkup = None
    KeyboardButton = None
    ReplyKeyboardMarkup = None


class TelegramSendMessageIntegration(BaseIntegration):
    """Интеграция для отправки сообщений в Telegram через python-telegram-bot."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_message",
            version="1.1.1",
            name="Telegram Send Message",
            description="Отправка текстового сообщения в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "text"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "text": {
                        "type": "string",
                        "title": "Message Text",
                        "description": "Текст сообщения"
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None
                    },
                    "inline_keyboard": {
                        "type": "array",
                        "title": "Inline Keyboard",
                        "description": "Массив массивов кнопок под сообщением. Каждая кнопка: {\"text\": \"...\", \"callback_data\": \"...\"} или {\"text\": \"...\", \"url\": \"...\"}",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "title": "Button Text"
                                    },
                                    "callback_data": {
                                        "type": "string",
                                        "title": "Callback Data"
                                    },
                                    "url": {
                                        "type": "string",
                                        "title": "URL"
                                    },
                                    "web_app": {
                                        "type": "object",
                                        "title": "Web App",
                                        "properties": {
                                            "url": {"type": "string"}
                                        }
                                    },
                                    "switch_inline_query": {
                                        "type": "string",
                                        "title": "Switch Inline Query"
                                    },
                                    "switch_inline_query_current_chat": {
                                        "type": "string",
                                        "title": "Switch Inline Query Current Chat"
                                    }
                                },
                                "required": ["text"]
                            }
                        }
                    },
                    "reply_keyboard": {
                        "type": "array",
                        "title": "Reply Keyboard",
                        "description": "Массив массивов кнопок клавиатуры. Каждая кнопка: {\"text\": \"...\"}",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "title": "Button Text"
                                    },
                                    "request_contact": {
                                        "type": "boolean",
                                        "title": "Request Contact",
                                        "default": False
                                    },
                                    "request_location": {
                                        "type": "boolean",
                                        "title": "Request Location",
                                        "default": False
                                    },
                                    "request_poll": {
                                        "type": "object",
                                        "title": "Request Poll",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": ["quiz", "regular"]
                                            }
                                        }
                                    }
                                },
                                "required": ["text"]
                            }
                        }
                    },
                    "resize_keyboard": {
                        "type": "boolean",
                        "title": "Resize Keyboard",
                        "description": "Уменьшить клавиатуру (только для reply_keyboard)",
                        "default": False
                    },
                    "one_time_keyboard": {
                        "type": "boolean",
                        "title": "One Time Keyboard",
                        "description": "Скрыть клавиатуру после использования (только для reply_keyboard)",
                        "default": False
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Простое сообщение",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "text": "Hello from DBCV!"
                    }
                },
                {
                    "title": "Сообщение с inline кнопками",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "text": "Выберите действие:",
                        "inline_keyboard": [
                            [
                                {"text": "Кнопка 1", "callback_data": "action_1"},
                                {"text": "Кнопка 2", "callback_data": "action_2"}
                            ],
                            [
                                {"text": "Открыть сайт", "url": "https://example.com"}
                            ]
                        ]
                    }
                },
                {
                    "title": "Сообщение с reply клавиатурой",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "text": "Выберите вариант:",
                        "reply_keyboard": [
                            [
                                {"text": "Вариант 1"},
                                {"text": "Вариант 2"}
                            ],
                            [
                                {"text": "Отмена"}
                            ]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": True
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
        text = config.get("text")
        parse_mode = config.get("parse_mode")
        inline_keyboard = config.get("inline_keyboard")
        reply_keyboard = config.get("reply_keyboard")
        resize_keyboard = config.get("resize_keyboard", False)
        one_time_keyboard = config.get("one_time_keyboard", False)
        
        if not chat_id or not text:
            await logger.error("chat_id and text are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and text are required"
                }
            }
        
        # Создаем клавиатуры, если они указаны
        reply_markup = None
        
        if inline_keyboard:
            # Создаем inline клавиатуру
            inline_keyboard_rows = []
            for row in inline_keyboard:
                button_row = []
                for button in row:
                    button_kwargs = {"text": str(button["text"])}
                    
                    if "callback_data" in button:
                        button_kwargs["callback_data"] = str(button["callback_data"])
                    elif "url" in button:
                        button_kwargs["url"] = str(button["url"])
                    elif "web_app" in button:
                        button_kwargs["web_app"] = button["web_app"]
                    elif "switch_inline_query" in button:
                        button_kwargs["switch_inline_query"] = str(button["switch_inline_query"])
                    elif "switch_inline_query_current_chat" in button:
                        button_kwargs["switch_inline_query_current_chat"] = str(button["switch_inline_query_current_chat"])
                    
                    button_row.append(InlineKeyboardButton(**button_kwargs))
                
                if button_row:
                    inline_keyboard_rows.append(button_row)
            
            if inline_keyboard_rows:
                reply_markup = InlineKeyboardMarkup(inline_keyboard_rows)
        
        elif reply_keyboard:
            # Создаем reply клавиатуру
            keyboard_rows = []
            for row in reply_keyboard:
                button_row = []
                for button in row:
                    button_kwargs = {"text": str(button["text"])}
                    
                    if button.get("request_contact"):
                        button_kwargs["request_contact"] = True
                    if button.get("request_location"):
                        button_kwargs["request_location"] = True
                    if "request_poll" in button:
                        button_kwargs["request_poll"] = button["request_poll"]
                    
                    button_row.append(KeyboardButton(**button_kwargs))
                
                if button_row:
                    keyboard_rows.append(button_row)
            
            if keyboard_rows:
                reply_markup = ReplyKeyboardMarkup(
                    keyboard_rows,
                    resize_keyboard=resize_keyboard,
                    one_time_keyboard=one_time_keyboard
                )
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            result = await bot.send_message(
                chat_id=str(chat_id),
                text=str(text),
                parse_mode=parse_mode if parse_mode else None,
                reply_markup=reply_markup
            )
            
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
                        "text": result.text,
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

