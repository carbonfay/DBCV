"""Gitverse интеграции."""
from .get_commits import GitverseGetCommitsIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграции
registry.register(GitverseGetCommitsIntegration())
