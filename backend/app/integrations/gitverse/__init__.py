"""Gitverse integrations package"""
from app.integrations.registry import registry

# Регистрируем все интеграции в этом пакете
try:
    from app.integrations.gitverse.get_merge_request import GitverseGetMergeRequestIntegration  # noqa: F401
    registry.register(GitverseGetMergeRequestIntegration())
except ImportError:
    # Библиотека PyGithub может быть не установлена в среде тестирования
    pass
