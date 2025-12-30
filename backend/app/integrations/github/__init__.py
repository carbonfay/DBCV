from .get_repo import GitHubGetRepositoryIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграции — создаём экземпляр и регистрируем
registry.register(GitHubGetRepositoryIntegration())

# Экспортируем имя класса, как в остальных интеграционных пакетах
__all__ = ["GitHubGetRepositoryIntegration"]