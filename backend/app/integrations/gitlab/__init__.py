"""GitLab интеграции."""
from .create_issue import GitLabCreateIssueIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GitLabCreateIssueIntegration())