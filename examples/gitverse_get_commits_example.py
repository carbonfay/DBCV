# Пример конфигурации для интеграции
config = {
    "project_id": "your-project-id",
    "ref_name": "main",
    "since": "2023-01-01T00:00:00Z"
}

# Вызов интеграции
from backend.app.integrations.gitverse.get_commits import GitVerseGetCommits
integration = GitVerseGetCommits()
result = integration.execute(config)

print(result)
