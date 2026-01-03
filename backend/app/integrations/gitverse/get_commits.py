from typing import Dict, Any
from backend.app.core.credentials import CredentialsResolver
import requests


class GitVerseGetCommits:
    id = "gitverse_get_commits"
    name = "Get Commits"
    description = "Получение списка коммитов из репозитория GitVerse (совместимо с GitLab API v4)"
    category = "Integrations"
    icon_s3_key = "icons/gitverse.png"
    version = "1.0.0"

    config_schema = {
        "required": ["project_id"],
        "properties": {
            "project_id": {
                "type": "string",
                "description": "ID проекта в GitVerse"
            },
            "ref_name": {
                "type": "string",
                "description": "Ветвь или тег (опционально)"
            },
            "since": {
                "type": "string",
                "format": "date-time",
                "description": "Фильтрация коммитов с указанной даты (опционально)"
            }
        }
    }

    def __init__(self):
        self.credentials = CredentialsResolver.get_credentials("gitverse")

    def execute(self, config: Dict[str, Any], payload=None) -> Dict[str, Any]:
        # Получение параметров из конфига
        project_id = config["project_id"]
        ref_name = config.get("ref_name")
        since = config.get("since")

        # Формирование URL запроса
        base_url = self.credentials["api_url"]  # Например, https://gitverse.example.com
        endpoint = f"/api/v4/projects/{project_id}/repository/commits"
        url = base_url + endpoint

        # Параметры запроса
        params = {}
        if ref_name:
            params["ref_name"] = ref_name
        if since:
            params["since"] = since

        # Выполнение запроса
        headers = {
            "Authorization": f"Bearer {self.credentials['token']}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
