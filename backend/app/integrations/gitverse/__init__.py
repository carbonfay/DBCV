from .get_commits import GitVerseGetCommits
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(GitVerseGetCommits())
