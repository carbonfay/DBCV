"""Базовый класс для пресетов."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from uuid import UUID

from app.integrations.base import IntegrationMetadata
from app.models.step import StepModel
from app.models.connection_group import ConnectionGroupModel
from app.models.connection import ConnectionModel
from app.models.message import MessageModel


class BasePreset(ABC):
    """Базовый класс для пресетов."""

    @property
    @abstractmethod
    def metadata(self) -> IntegrationMetadata:
        """Метаданные пресета."""
        pass

    @abstractmethod
    def build(
        self,
        config: Dict[str, Any],
        bot_id: UUID
    ) -> Dict[str, Any]:
        """
        Создает структуры для интеграции: Step, ConnectionGroup, Connections и т.д.
        
        Args:
            config: Параметры пресета
            bot_id: ID бота
            
        Returns:
            Словарь с созданными сущностями
        """
        pass