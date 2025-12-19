"""Telegram Send Document интеграция используя python-telegram-bot библиотеку."""
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


class TelegramSendDocumentIntegration(BaseIntegration):
    """Интеграция для отправки документов в Telegram через Bot API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_document",
            version="1.0.0",
            name="Telegram Send Document",
            description="Отправка документов в Telegram через Bot API",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#229ED9",
            config_schema={
                "type": "object",
                "required": ["chat_id", "document"],
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "title": "Chat ID",
                        "description": "ID чата или пользователя для отправки документа"
                    },
                    "document": {
                        "type": "string",
                        "title": "Document",
                        "description": "Документ для отправки (URL или base64 encoded файл)"
                    },
                    "caption": {
                        "type": "string",
                        "title": "Caption",
                        "description": "Подпись к документу"
                    },
                    "parse_mode": {
                        "type": "string",
                        "title": "Parse Mode",
                        "description": "Режим парсинга для форматирования текста",
                        "enum": ["HTML", "Markdown", "MarkdownV2"],
                        "default": "HTML"
                    },
                    "disable_notification": {
                        "type": "boolean",
                        "title": "Disable Notification",
                        "description": "Отправить без уведомления",
                        "default": False
                    },
                    "protect_content": {
                        "type": "boolean",
                        "title": "Protect Content",
                        "description": "Защитить содержимое от копирования",
                        "default": False
                    },
                    "reply_to_message_id": {
                        "type": "integer",
                        "title": "Reply To Message ID",
                        "description": "ID сообщения, на которое нужно ответить"
                    },
                    "allow_sending_without_reply": {
                        "type": "boolean",
                        "title": "Allow Sending Without Reply",
                        "description": "Разрешить отправку если reply_to_message_id не найдено",
                        "default": False
                    },
                    "thumb": {
                        "type": "string",
                        "title": "Thumbnail",
                        "description": "Миниатюра для документа (URL или base64)"
                    },
                    "file_name": {
                        "type": "string",
                        "title": "File Name",
                        "description": "Имя файла для отображения"
                    }
                }
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправить документ пользователю",
                    "config": {
                        "chat_id": "{$user.telegram_chat_id$}",
                        "document": "{$session.document_url$}",
                        "caption": "Документ для вас",
                        "disable_notification": False
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
            await logger.error(f"Bot token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Bot token not found in credentials"
                }
            }

        # Получаем параметры из config
        chat_id = config.get("chat_id")
        document = config.get("document")
        caption = config.get("caption")
        parse_mode = config.get("parse_mode")
        disable_notification = config.get("disable_notification", False)
        protect_content = config.get("protect_content", False)
        reply_to_message_id = config.get("reply_to_message_id")
        allow_sending_without_reply = config.get("allow_sending_without_reply", False)
        thumb = config.get("thumb")
        file_name = config.get("file_name")

        if not chat_id or not document:
            await logger.error("chat_id and document are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and document are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)

            # Подготовим дополнительные параметры
            extra_args = {}
            if caption:
                extra_args["caption"] = caption
            if parse_mode:
                extra_args["parse_mode"] = parse_mode
            if disable_notification:
                extra_args["disable_notification"] = disable_notification
            if protect_content:
                extra_args["protect_content"] = protect_content
            if reply_to_message_id:
                extra_args["reply_to_message_id"] = reply_to_message_id
            if allow_sending_without_reply:
                extra_args["allow_sending_without_reply"] = allow_sending_without_reply
            if thumb:
                extra_args["thumb"] = thumb
            if file_name:
                extra_args["filename"] = file_name

            # Проверим, является ли document URL или base64
            if document.startswith('http'):
                # Это URL, отправляем как есть
                result = await bot.send_document(
                    chat_id=chat_id,
                    document=document,
                    **extra_args
                )
            else:
                # Это может быть base64 или file_id
                try:
                    # Попробуем отправить как base64
                    import base64
                    import io
                    
                    # Декодируем base64 для проверки
                    decoded_bytes = base64.b64decode(document)
                    
                    # Создаем байтовый поток
                    document_stream = io.BytesIO(decoded_bytes)
                    
                    result = await bot.send_document(
                        chat_id=chat_id,
                        document=document_stream,
                        **extra_args
                    )
                except Exception:
                    # Если ошибка декодирования, предполагаем, что это file_id
                    result = await bot.send_document(
                        chat_id=chat_id,
                        document=document,
                        **extra_args
                    )

            # Подготовим результат в формате системы
            response_data = {
                "message_id": result.message_id,
                "date": result.date,
                "chat": {
                    "id": result.chat.id,
                    "type": result.chat.type,
                    "title": getattr(result.chat, 'title', None),
                    "username": result.chat.username,
                    "first_name": getattr(result.chat, 'first_name', None),
                    "last_name": getattr(result.chat, 'last_name', None)
                },
                "document": {
                    "file_id": result.document.file_id,
                    "file_unique_id": result.document.file_unique_id,
                    "file_name": result.document.file_name,
                    "mime_type": result.document.mime_type,
                    "file_size": result.document.file_size,
                    "thumb": {
                        "file_id": result.document.thumb.file_id if result.document.thumb else None,
                        "file_unique_id": result.document.thumb.file_unique_id if result.document.thumb else None,
                        "width": result.document.thumb.width if result.document.thumb else None,
                        "height": result.document.thumb.height if result.document.thumb else None,
                        "file_size": result.document.thumb.file_size if result.document.thumb else None
                    } if result.document.thumb else None
                },
                "caption": result.caption,
                "caption_entities": [
                    {
                        "type": entity.type,
                        "offset": entity.offset,
                        "length": entity.length,
                        "url": entity.url,
                        "user": {
                            "id": entity.user.id,
                            "is_bot": entity.user.is_bot,
                            "first_name": entity.user.first_name,
                            "last_name": entity.user.last_name,
                            "username": entity.user.username
                        } if entity.user else None
                    } for entity in result.caption_entities
                ] if hasattr(result, 'caption_entities') and result.caption_entities else []
            }

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": response_data
                }
            }
        except TelegramError as e:
            await logger.error(f"Telegram API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.error_code if hasattr(e, 'error_code') else 500,
                    "description": f"Telegram API error: {str(e)}"
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

