"""Telegram Send Inline Keyboard интеграция используя python-telegram-bot библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.error import TelegramError
    TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    TELEGRAM_BOT_AVAILABLE = False
    Bot = None
    InlineKeyboardMarkup = None
    InlineKeyboardButton = None
    TelegramError = Exception


class TelegramSendInlineKeyboardIntegration(BaseIntegration):
    """Интеграция для отправки сообщения с inline клавиатурой в Telegram через Bot API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_inline_keyboard",
            version="1.0.0",
            name="Telegram Send Inline Keyboard",
            description="Отправка сообщения с интерактивной inline клавиатурой в Telegram",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": ["chat_id", "text", "keyboard"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя (можно использовать переменные: {$user.telegram_chat_id$})"
                    },
                    "text": {
                        "type": "string",
                        "title": "Text",
                        "description": "Текст сообщения для отправки с клавиатурой"
                    },
                    "keyboard": {
                        "type": "array",
                        "title": "Keyboard",
                        "description": "Массив кнопок клавиатуры",
                        "items": {
                            "type": "array",
                            "title": "Row",
                            "description": "Ряд кнопок",
                            "items": {
                                "type": "object",
                                "title": "Button",
                                "required": ["text", "callback_data"],
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "title": "Button Text",
                                        "description": "Текст на кнопке"
                                    },
                                    "callback_data": {
                                        "type": "string",
                                        "title": "Callback Data",
                                        "description": "Данные, отправляемые при нажатии кнопки"
                                    }
                                }
                            }
                        }
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": None
                    },
                    "disable_notification": {
                        "type": "boolean",
                        "title": "Disable Notification",
                        "description": "Отправить без уведомления",
                        "default": False
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправить сообщение с меню выбора",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "text": "Выберите действие:",
                        "keyboard": [
                            [
                                {"text": "Да", "callback_data": "yes"},
                                {"text": "Нет", "callback_data": "no"}
                            ],
                            [
                                {"text": "Отмена", "callback_data": "cancel"}
                            ]
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
        keyboard_config = config.get("keyboard")
        parse_mode = config.get("parse_mode")
        disable_notification = config.get("disable_notification", False)

        if not chat_id or not text or not keyboard_config:
            await logger.error("chat_id, text and keyboard are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id, text and keyboard are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            
            # Создаем inline клавиатуру из конфигурации
            keyboard_rows = []
            for row_config in keyboard_config:
                row_buttons = []
                for button_config in row_config:
                    button = InlineKeyboardButton(
                        text=button_config["text"],
                        callback_data=button_config["callback_data"]
                    )
                    row_buttons.append(button)
                keyboard_rows.append(row_buttons)
            
            inline_keyboard = InlineKeyboardMarkup(keyboard_rows)

            # Отправляем сообщение с inline клавиатурой
            result = await bot.send_message(
                chat_id=str(chat_id),
                text=str(text),
                reply_markup=inline_keyboard,
                parse_mode=parse_mode if parse_mode else None,
                disable_notification=disable_notification
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
                        "date": result.date,
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": button.text,
                                        "callback_data": button.callback_data
                                    } for button in row
                                ] for row in keyboard_rows
                            ]
                        }
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

