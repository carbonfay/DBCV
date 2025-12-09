
from typing import Any, Dict, Optional
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class TelegramSendMessageIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_send_message",
            version="1.0.1",
            name="Telegram Send Message",
            description="Отправка сообщения в Telegram через python-telegram-bot.",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "ID чата или username",
                    },
                    "text": {
                        "type": "string",
                        "description": "Текст сообщения",
                    },
                    "parse_mode": {
                        "type": "string",
                        "enum": ["Markdown", "HTML"],
                        "description": "Режим форматирования",
                    },
                },
                "required": ["chat_id", "text"],
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot",
            examples=[
                {
                    "config": {"chat_id": "@username", "text": "Привет!"},
                    "description": "Отправить простое сообщение",
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """
        Отправляет сообщение в Telegram, используя python-telegram-bot.
        """
        chat_id = config.get("chat_id")
        text = config.get("text")
        parse_mode = config.get("parse_mode")

        if not chat_id or not text:
            await logger.error("chat_id and text are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "chat_id and text are required",
                }
            }

        # Получаем credentials для Telegram
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key",
        )

        if not creds:
            await logger.error("Telegram credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram credentials not found",
                }
            }

        payload = creds.get("payload") or {}
        # Поддерживаем оба возможных ключа токена, с учётом вложенного payload
        bot_token = (
            creds.get("bot_token")
            or creds.get("api_key")
            or payload.get("bot_token")
            or payload.get("api_key")
        )
        if not bot_token:
            await logger.error("Telegram bot token not found in credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram bot token not found in credentials",
                }
            }

        # Локальный импорт, чтобы каталог интеграций работал даже без установленной библиотеки
        try:
            from telegram import Bot, TelegramError  # type: ignore
        except ImportError:
            await logger.warning(
                "python-telegram-bot is missing; falling back to Telegram HTTP API"
            )
            return await self._send_via_http_api(
                bot_token=bot_token,
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                logger=logger,
            )

        bot = Bot(token=bot_token)

        try:
            # В python-telegram-bot v20+ методы являются асинхронными
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
            )

            # Формируем результат вручную, чтобы быть совместимыми с тестами
            chat = getattr(message, "chat", None)
            result_payload: Dict[str, Any] = {
                "message_id": getattr(message, "message_id", None),
                "chat": {
                    "id": getattr(chat, "id", None) if chat else None,
                    "type": getattr(chat, "type", None) if chat else None,
                },
                "text": getattr(message, "text", None),
                "date": getattr(message, "date", None),
            }

            return {"response": {"ok": True, "result": result_payload}}

        except TelegramError as e:
            await logger.error(f"TelegramError while sending message: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while sending message: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }

    async def _send_via_http_api(
        self,
        bot_token: str,
        chat_id: str,
        text: str,
        parse_mode: Optional[str],
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Запасной путь через официальный Telegram HTTP API, если библиотека не установлена."""
        import httpx

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            await logger.error(
                f"Telegram HTTP error: {exc.response.status_code} {exc.response.text}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": exc.response.status_code,
                    "description": exc.response.text,
                }
            }
        except Exception as exc:
            await logger.error(
                f"Unexpected error while sending message via HTTP: {exc}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(exc),
                }
            }

        if not data.get("ok"):
            await logger.error(f"Telegram API responded with error: {data}")
            return {
                "response": {
                    "ok": False,
                    "error_code": data.get("error_code", 500),
                    "description": data.get("description")
                    or data.get("error_message")
                    or "Telegram API error",
                }
            }

        result = data.get("result", {})
        return {
            "response": {
                "ok": True,
                "result": {
                    "message_id": result.get("message_id"),
                    "chat": result.get("chat"),
                    "text": result.get("text"),
                    "date": result.get("date"),
                },
            }
        }
