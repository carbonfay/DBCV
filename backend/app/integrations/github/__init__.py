from app.integrations.github.get_repository import GitHubGetRepositoryIntegration
from app.integrations.registry import registry

registry.register(GitHubGetRepositoryIntegration())

__all__ = [
    "GitHubGetRepositoryIntegration",
]
