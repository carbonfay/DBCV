# backend/app/integrations/gitverse/get_commits.py

from integrations.base import BaseIntegration
from integrations.credentials import credentials_resolver
import logging

# Если SAFE_LIBRARIES.md разрешает requests, используем её
import requests

logger = logging.getLogger(__name__)

class GitVerseGetCommits(BaseIntegration):
    """
    Интеграция GitVerse: Получение списка коммитов из репозитория.
    """

    # Метаданные интеграции
    name = "gitverse.get_commits"
    description = "Получает список коммитов из GitVerse репозитория"
    version = "1.0.0"

    def execute(self, repo_url: str, branch: str = "main", max_commits: int = 10):
        """
        Получает коммиты из репозитория.

        :param repo_url: URL репозитория
        :param branch: Ветка, по умолчанию main
        :param max_commits: Максимальное количество коммитов для получения
        :return: Список коммитов или dict с ошибкой
        """
        try:
            # Получаем credentials
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

            # Запрос к GitVerse API
            response = requests.get(
                f"{repo_url}/commits?branch={branch}&limit={max_commits}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()  # выбросит исключение для HTTP ошибок

            commits = response.json()
            return {"commits": commits}

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к GitVerse API: {e}")
            return {"error": f"Ошибка запроса: {str(e)}"}
        except Exception as e:
            logger.exception("Неизвестная ошибка в GitVerseGetCommits")
            return {"error": f"Неизвестная ошибка: {str(e)}"}
