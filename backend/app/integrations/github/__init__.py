from .get_pull_request import GitHubGetPullRequestIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций — создаём экземпляры и регистрируем
registry.register(GitHubGetPullRequestIntegration())

# Экспортируем имена классов
__all__ = ["GitHubGetPullRequestIntegration"]