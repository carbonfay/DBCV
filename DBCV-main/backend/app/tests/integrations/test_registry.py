"""Тесты для IntegrationRegistry."""
import pytest

from app.integrations.registry import IntegrationRegistry
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.tests.integrations.test_base import TestIntegration


@pytest.fixture
def registry():
    """Создает новый реестр для тестов."""
    return IntegrationRegistry()


@pytest.fixture
def integration():
    """Создает тестовую интеграцию."""
    return TestIntegration()


def test_registry_register(registry, integration):
    """Тест регистрации интеграции."""
    registry.register(integration)
    
    # Проверяем, что интеграция зарегистрирована
    result = registry.get("test_integration")
    assert result is not None
    assert result.metadata.id == "test_integration"


def test_registry_get_latest_version(registry, integration):
    """Тест получения последней версии интеграции."""
    registry.register(integration, version="1.0.0")
    
    # Создаем новую версию
    integration_v2 = TestIntegration()
    registry.register(integration_v2, version="2.0.0")
    
    # Должна вернуться последняя версия
    result = registry.get("test_integration")
    assert result.metadata.version == "2.0.0"


def test_registry_get_specific_version(registry, integration):
    """Тест получения конкретной версии интеграции."""
    registry.register(integration, version="1.0.0")
    
    integration_v2 = TestIntegration()
    registry.register(integration_v2, version="2.0.0")
    
    # Получаем конкретную версию
    result = registry.get("test_integration", version="1.0.0")
    assert result.metadata.version == "1.0.0"


def test_registry_list_all(registry, integration):
    """Тест получения списка всех интеграций."""
    registry.register(integration)
    
    all_integrations = registry.list_all()
    assert len(all_integrations) >= 1
    assert any(meta.id == "test_integration" for meta in all_integrations)


def test_registry_list_by_category(registry, integration):
    """Тест получения интеграций по категории."""
    registry.register(integration)
    
    test_integrations = registry.list_by_category("test")
    assert len(test_integrations) >= 1
    assert all(meta.category == "test" for meta in test_integrations)


def test_registry_get_nonexistent(registry):
    """Тест получения несуществующей интеграции."""
    result = registry.get("nonexistent")
    assert result is None

