"""Реестр всех доступных интеграций с версионированием."""
from typing import Dict, List, Optional, Tuple
from .base import BaseIntegration, IntegrationMetadata


class IntegrationRegistry:
    """Реестр всех доступных интеграций с версионированием."""
    
    def __init__(self):
        # Храним по ключу (id, version)
        self._integrations: Dict[Tuple[str, str], BaseIntegration] = {}
        # Последние версии для быстрого доступа
        self._latest_versions: Dict[str, str] = {}
    
    def register(self, integration: BaseIntegration, version: Optional[str] = None):
        """
        Регистрирует интеграцию.
        
        Args:
            integration: Экземпляр интеграции
            version: Версия (если не указана, берется из metadata)
        """
        metadata = integration.metadata
        version = version or metadata.version
        key = (metadata.id, version)
        self._integrations[key] = integration
        
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
        integration_id: str,
        version: Optional[str] = None
    ) -> Optional[BaseIntegration]:
        """
        Получает интеграцию по ID и версии.
        
        Args:
            integration_id: ID интеграции
            version: Версия (если не указана, возвращается последняя)
        
        Returns:
            Экземпляр интеграции или None
        """
        if version:
            return self._integrations.get((integration_id, version))
        # Возвращаем последнюю версию
        latest_version = self._latest_versions.get(integration_id)
        if latest_version:
            return self._integrations.get((integration_id, latest_version))
        return None
    
    def list_all(self, latest_only: bool = True) -> List[IntegrationMetadata]:
        """
        Возвращает список всех метаданных.
        
        Args:
            latest_only: Если True, возвращает только последние версии
        
        Returns:
            Список метаданных интеграций
        """
        if latest_only:
            return [
                self._integrations[(id, self._latest_versions[id])].metadata
                for id in self._latest_versions.keys()
            ]
        return [integration.metadata for integration in self._integrations.values()]
    
    def list_by_category(
        self,
        category: str,
        latest_only: bool = True
    ) -> List[IntegrationMetadata]:
        """
        Возвращает интеграции по категории.
        
        Args:
            category: Категория (messaging, ai, storage и т.д.)
            latest_only: Если True, возвращает только последние версии
        
        Returns:
            Список метаданных интеграций категории
        """
        all_metadata = self.list_all(latest_only=latest_only)
        return [
            metadata
            for metadata in all_metadata
            if metadata.category == category
        ]


# Глобальный реестр
registry = IntegrationRegistry()

