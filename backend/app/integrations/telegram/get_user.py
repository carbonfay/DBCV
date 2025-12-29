"""Telegram Get User интеграция используя python-telegram-bot библиотеку."""
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


class TelegramGetUserIntegration(BaseIntegration):
    """Интеграция для получения информации о боте через Telegram Bot API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="telegram_get_user",
            version="1.0.0",
            name="Telegram Get User",
            description="Получение информации о боте через Bot API (getMe)",
            category="messaging",
            icon_s3_key="icons/integrations/telegram.svg",
            color="#0088cc",
            config_schema={
                "type": "object",
                "required": [],
                "properties": {}
            },
            credentials_provider="telegram",
            credentials_strategy="api_key",
            library_name="python-telegram-bot>=20.0" if TELEGRAM_BOT_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о боте",
                    "config": {}
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
            config: Параметры интеграции (не требуются для getMe)
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
        # Сначала пытаемся получить default credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="telegram",
            strategy="api_key"
        )
        
        # Если default не найден, пытаемся получить любые credentials для этого provider
        if not creds or (isinstance(creds, dict) and not creds.get("payload") and not creds.get("bot_token") and not creds.get("token")):
            await logger.warning("Default Telegram credentials not found, trying to get any credentials")
            creds = await credentials_resolver.get_single_for(
                bot_id=bot_id,
                provider="telegram",
                strategy="api_key"
            )
        
        if not creds or (isinstance(creds, dict) and len(creds) == 0):
            await logger.error(f"Telegram credentials not found for bot_id={bot_id}, provider=telegram, strategy=api_key")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Telegram credentials not found. Please create credentials with provider='telegram', strategy='api_key' and set is_default=true"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        bot_token = payload.get("bot_token") or payload.get("token")
        if not bot_token:
            await logger.error(f"bot_token not found in credentials. Creds keys: {list(creds.keys())}, Payload keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"bot_token not found in credentials payload. Expected 'bot_token' or 'token' key in payload. Available keys: {list(payload.keys())}"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            bot = Bot(token=bot_token)
            user = await bot.get_me()
            
            # Преобразуем объект User в словарь
            # Используем to_dict() если доступен, иначе создаем словарь вручную
            if hasattr(user, 'to_dict'):
                user_dict = user.to_dict()
            else:
                user_dict = {
                    "id": user.id,
                    "is_bot": user.is_bot,
                    "first_name": user.first_name,
                    "last_name": getattr(user, 'last_name', None),
                    "username": getattr(user, 'username', None),
                    "language_code": getattr(user, 'language_code', None),
                    "can_join_groups": getattr(user, 'can_join_groups', None),
                    "can_read_all_group_messages": getattr(user, 'can_read_all_group_messages', None),
                    "supports_inline_queries": getattr(user, 'supports_inline_queries', None)
                }
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": user_dict
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

