"""Реестр всех доступных presets."""
from typing import Dict, List, Optional
from .base import BasePreset, PresetMetadata


class PresetRegistry:
    """Реестр всех доступных presets."""
    
    def __init__(self):
        self._presets: Dict[str, BasePreset] = {}
    
    def register(self, preset: BasePreset):
        """
        Регистрирует preset.
        
        Args:
            preset: Экземпляр preset
        """
        metadata = preset.metadata
        self._presets[metadata.id] = preset
    
    def get(self, preset_id: str) -> Optional[BasePreset]:
        """
        Получает preset по ID.
        
        Args:
            preset_id: ID preset
        
        Returns:
            Экземпляр preset или None
        """
        return self._presets.get(preset_id)
    
    def list_all(self) -> List[PresetMetadata]:
        """
        Возвращает список всех метаданных.
        
        Returns:
            Список метаданных presets
        """
        return [preset.metadata for preset in self._presets.values()]
    
    def list_by_category(self, category: str) -> List[PresetMetadata]:
        """
        Возвращает presets по категории.
        
        Args:
            category: Категория (logic, flow, integration и т.д.)
        
        Returns:
            Список метаданных presets категории
        """
        return [
            preset.metadata
            for preset in self._presets.values()
            if preset.metadata.category == category
        ]


# Глобальный реестр
registry = PresetRegistry()

