"""Базовые классы для интеграций."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import UUID
from dataclasses import dataclass

from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@dataclass
class IntegrationMetadata:
    """Метаданные интеграции для фронтенда."""
    id: str  # "telegram_send_message"
    version: str  # "1.0.0"
    name: str  # "Telegram Send Message"
    description: str  # Описание
    category: str  # "messaging", "ai", "storage", "weather", "maps", "payments", "crm", "ecommerce", "education", "medicine", "news", "translation"
    icon_s3_key: str  # "icons/integrations/telegram.svg"
    color: str  # "#0088cc"
    config_schema: dict  # JSON Schema для параметров
    credentials_provider: str  # "telegram" для CredentialEntity
    credentials_strategy: str  # "api_key" или "oauth"
    library_name: Optional[str] = None  # "python-telegram-bot" если используется
    examples: Optional[List[dict]] = None  # Примеры использования


class BaseIntegration(ABC):
    """Базовый класс для интеграций с поддержкой библиотек."""
    
    @property
    @abstractmethod
    def metadata(self) -> IntegrationMetadata:
        """Метаданные интеграции."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя библиотеку внутри backend кода.
        
        Args:
            config: Параметры интеграции (из config_schema)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер для записи логов
        
        Returns:
            dict с результатом выполнения в формате:
            {
                "response": {
                    "ok": True/False,
                    "result": {...} или "error": "..."
                }
            }
        """
        pass

