"""GitHub интеграции и автоматическая регистрация."""
from .get_repository import GitHubGetRepositoryIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграции
registry.register(GitHubGetRepositoryIntegration())

__all__ = ["GitHubGetRepositoryIntegration"]
