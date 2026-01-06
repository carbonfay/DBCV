"""Базовые классы для presets."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from dataclasses import dataclass

from app.schemas.step import StepCreate
from app.schemas.connection import ConnectionGroupCreate


@dataclass
class PresetMetadata:
    """Метаданные preset для фронтенда."""
    id: str  # "if", "switch", "delay" и т.д.
    name: str  # "IF/ELSE"
    description: str  # Описание
    category: str  # "logic", "flow", "integration" и т.д.
    icon_s3_key: str  # "icons/presets/if.svg"
    color: str  # "#4CAF50"
    config_schema: dict  # JSON Schema для параметров
    examples: Optional[List[dict]] = None  # Примеры использования


class BasePreset(ABC):
    """Базовый класс для presets."""
    
    @property
    @abstractmethod
    def metadata(self) -> PresetMetadata:
        """Метаданные preset."""
        pass
    
    @abstractmethod
    async def build(
        self,
        bot_id: Union[UUID, str],
        config: Dict[str, Any],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает структуру Step + ConnectionGroup + Connections.
        
        Args:
            bot_id: ID бота
            config: Параметры preset (из config_schema)
            name: Имя шага (опционально, может быть переопределено из config)
        
        Returns:
            dict с ключами:
            {
                "step": StepCreate,
                "connection_group": ConnectionGroupCreate
            }
        """
        pass

