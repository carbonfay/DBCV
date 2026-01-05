from integrations.base import BaseIntegration
from integrations.credentials import credentials_resolver
import logging
import requests

logger = logging.getLogger(__name__)

class GitVerseGetCommits(BaseIntegration):
    name = "gitverse.get_commits"
    description = "Получает список коммитов из GitVerse репозитория"
    version = "1.0.0"

    def execute(self, repo_url: str, branch: str = "main", max_commits: int = 10):
        try:
            creds = credentials_resolver.get_default_for(
                provider="gitverse",
                strategy="api_token"
            )
            if not creds or "token" not in creds:
                error_msg = "Не удалось получить credentials для GitVerse"
                logger.error(error_msg)
                return {"error": error_msg}

            headers = {
                "Authorization": f"Bearer {creds['token']}",
                "Accept": "application/json"
            }

            response = requests.get(
                f"{repo_url}/commits?branch={branch}&limit={max_commits}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            commits = response.json()
            return {"commits": commits}

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к GitVerse API: {e}")
            return {"error": f"Ошибка запроса: {str(e)}"}
        except Exception as e:
            logger.exception("Неизвестная ошибка в GitVerseGetCommits")
            return {"error": f"Неизвестная ошибка: {str(e)}"}
