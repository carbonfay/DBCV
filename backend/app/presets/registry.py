"""Реестр пресетов для DBCV."""
from typing import Dict, List, Optional, Tuple
from .base import BasePreset, IntegrationMetadata


class PresetRegistry:
    """Реестр всех доступных пресетов с версионированием."""

    def __init__(self):
        # Храним по ключу (id, version)
        self._presets: Dict[Tuple[str, str], BasePreset] = {}
        # Последние версии для быстрого доступа
        self._latest_versions: Dict[str, str] = {}

    def register(self, preset: BasePreset, version: Optional[str] = None):
        """
        Регистрирует пресет.

        Args:
            preset: Экземпляр пресета
            version: Версия (если не указана, берется из metadata)
        """
        metadata = preset.metadata
        version = version or metadata.version
        key = (metadata.id, version)
        self._presets[key] = preset

        # Обновляем последнюю версию
        if metadata.id not in self._latest_versions:
            self._latest_versions[metadata.id] = version
        else:
            # Сравниваем версии (простое сравнение строк, можно улучшить)
            current_latest = self._latest_versions[metadata.id]
            if version > current_latest:
                self._latest_versions[metadata.id] = version

    def get(
        self,
        preset_id: str,
        version: Optional[str] = None
    ) -> Optional[BasePreset]:
        """
        Получает пресет по ID и версии.

        Args:
            preset_id: ID пресета
            version: Версия (если не указана, возвращается последняя)

        Returns:
            Экземпляр пресета или None
        """
        if version:
            return self._presets.get((preset_id, version))
        # Возвращаем последнюю версия
        latest_version = self._latest_versions.get(preset_id)
        if latest_version:
            return self._presets.get((preset_id, latest_version))
        return None

    def list_all(self, latest_only: bool = True) -> List[IntegrationMetadata]:
        """
        Возвращает список всех метаданных.

        Args:
            latest_only: Если True, возвращает только последние версии

        Returns:
            Список метаданных пресетов
        """
        if latest_only:
            return [
                self._presets[(id, self._latest_versions[id])].metadata
                for id in self._latest_versions.keys()
            ]
        return [preset.metadata for preset in self._presets.values()]

    def list_by_category(
        self,
        category: str,
        latest_only: bool = True
    ) -> List[IntegrationMetadata]:
        """
        Возвращает пресеты по категории.

        Args:
            category: Категория
            latest_only: Если True, возвращает только последние версии

        Returns:
            Список метаданных пресетов категории
        """
        all_metadata = self.list_all(latest_only=latest_only)
        return [
            metadata
            for metadata in all_metadata
            if metadata.category == category
        ]


# Глобальный реестр
registry = PresetRegistry()