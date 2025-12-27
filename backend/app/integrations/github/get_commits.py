"""GitHub Get Commits интеграция используя httpx для прямых HTTP запросов."""
import httpx
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class GitHubGetCommitsIntegration(BaseIntegration):
    """Интеграция для получения списка коммитов из репозитория GitHub."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_commits",
            version="1.0.0",
            name="GitHub Get Commits",
            description="Получение списка коммитов из репозитория GitHub",
            category="development",
            icon_s3_key="icons/integrations/github.svg",
            color="#181717",
            config_schema={
                "type": "object",
                "required": ["owner", "repo"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Repository Owner",
                        "description": "Владелец репозитория (например, 'octocat')"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository Name",
                        "description": "Название репозитория (например, 'Hello-World')"
                    },
                    "sha": {
                        "type": "string",
                        "title": "Branch/Tag/SHA",
                        "description": "Branch, tag или SHA коммита для получения (по умолчанию 'main')"
                    },
                    "path": {
                        "type": "string",
                        "title": "File Path",
                        "description": "Путь к файлу для фильтрации коммитов, затрагивающих этот файл"
                    },
                    "author": {
                        "type": "string",
                        "title": "Author",
                        "description": "Фильтр по автору коммита (логин пользователя GitHub)"
                    }
                }
            },
            credentials_provider="github",
            credentials_strategy="api_key",
            library_name="httpx",
            examples=[
                {
                    "title": "Получить коммиты из репозитория",
                    "config": {
                        "owner": "octocat",
                        "repo": "Hello-World"
                    }
                },
                {
                    "title": "Получить коммиты из ветки develop",
                    "config": {
                        "owner": "mycompany",
                        "repo": "myproject",
                        "sha": "develop"
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя прямые HTTP запросы к GitHub API.

        Args:
            config: Параметры интеграции (owner, repo, sha, path, author)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        # Получаем API токен из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="github",  # Используем "github" как провайдер
            strategy="api_key"
        )

        token = None
        if creds:
            # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
            payload = creds.get("payload", {})
            if not payload:
                # Если payload нет, возможно данные в корне (для обратной совместимости)
                payload = creds

            token = payload.get("api_key") or payload.get("token")

        # Получаем параметры из config
        owner = config.get("owner")
        repo = config.get("repo")
        sha = config.get("sha", "main")  # По умолчанию используем ветку 'main'
        path = config.get("path")
        author = config.get("author")

        if not owner or not repo:
            await logger.error("owner and repo are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner and repo are required"
                }
            }

        # Формируем URL для запроса к GitHub API
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"

        # Подготавливаем параметры запроса
        params = {}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if author:
            params["author"] = author

        # Подготавливаем заголовки
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DBCV-GitHub-Integration"
        }
        
        # Добавляем токен авторизации, если он есть
        if token:
            headers["Authorization"] = f"token {token}"

        # Логируем параметры для отладки
        await logger.info(f"Making request to GitHub API for repo: {owner}/{repo}")

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ для HTTP запроса
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)

            if response.status_code == 401:
                error_content = response.text
                await logger.error(f"GitHub API returned status {response.status_code} - Unauthorized: {error_content}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "Unauthorized. Please check your GitHub API token."
                    }
                }

            if response.status_code == 403:
                error_content = response.text
                await logger.error(f"GitHub API returned status {response.status_code} - Forbidden: {error_content}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 403,
                        "description": "Forbidden. API rate limit exceeded or insufficient permissions."
                    }
                }

            if response.status_code == 404:
                error_content = response.text
                await logger.error(f"GitHub API returned status {response.status_code} - Not Found: {error_content}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": f"Repository {owner}/{repo} not found or no commits exist."
                    }
                }

            if response.status_code != 200:
                error_content = response.text
                await logger.error(f"GitHub API returned status {response.status_code} with content: {error_content}")
                # Try to parse error response as JSON to get more details
                try:
                    error_json = response.json()
                    error_message = error_json.get("message", error_content)
                except:
                    error_message = error_content
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"GitHub API error: {error_message}"
                    }
                }

            # Парсим JSON ответ
            commits = response.json()

            # Обрабатываем список коммитов
            processed_commits = []
            for commit_data in commits:
                commit_info = {
                    "sha": commit_data.get("sha"),
                    "url": commit_data.get("url"),
                    "message": commit_data.get("commit", {}).get("message"),
                    "author": {
                        "name": commit_data.get("commit", {}).get("author", {}).get("name"),
                        "email": commit_data.get("commit", {}).get("author", {}).get("email"),
                        "date": commit_data.get("commit", {}).get("author", {}).get("date")
                    },
                    "committer": {
                        "name": commit_data.get("commit", {}).get("committer", {}).get("name"),
                        "email": commit_data.get("commit", {}).get("committer", {}).get("email"),
                        "date": commit_data.get("commit", {}).get("committer", {}).get("date")
                    },
                    "tree": {
                        "sha": commit_data.get("commit", {}).get("tree", {}).get("sha"),
                        "url": commit_data.get("commit", {}).get("tree", {}).get("url")
                    },
                    "comment_count": commit_data.get("commit", {}).get("comment_count"),
                    "verification": commit_data.get("commit", {}).get("verification"),
                    "html_url": commit_data.get("html_url"),
                    "comments_url": commit_data.get("comments_url"),
                    "author_info": {
                        "login": commit_data.get("author", {}).get("login") if commit_data.get("author") else None,
                        "id": commit_data.get("author", {}).get("id") if commit_data.get("author") else None,
                        "avatar_url": commit_data.get("author", {}).get("avatar_url") if commit_data.get("author") else None,
                        "gravatar_id": commit_data.get("author", {}).get("gravatar_id") if commit_data.get("author") else None,
                        "url": commit_data.get("author", {}).get("url") if commit_data.get("author") else None,
                        "html_url": commit_data.get("author", {}).get("html_url") if commit_data.get("author") else None,
                        "followers_url": commit_data.get("author", {}).get("followers_url") if commit_data.get("author") else None,
                        "following_url": commit_data.get("author", {}).get("following_url") if commit_data.get("author") else None,
                        "gists_url": commit_data.get("author", {}).get("gists_url") if commit_data.get("author") else None,
                        "starred_url": commit_data.get("author", {}).get("starred_url") if commit_data.get("author") else None,
                        "subscriptions_url": commit_data.get("author", {}).get("subscriptions_url") if commit_data.get("author") else None,
                        "organizations_url": commit_data.get("author", {}).get("organizations_url") if commit_data.get("author") else None,
                        "repos_url": commit_data.get("author", {}).get("repos_url") if commit_data.get("author") else None,
                        "events_url": commit_data.get("author", {}).get("events_url") if commit_data.get("author") else None,
                        "received_events_url": commit_data.get("author", {}).get("received_events_url") if commit_data.get("author") else None,
                        "type": commit_data.get("author", {}).get("type") if commit_data.get("author") else None,
                        "site_admin": commit_data.get("author", {}).get("site_admin") if commit_data.get("author") else None
                    },
                    "committer_info": {
                        "login": commit_data.get("committer", {}).get("login") if commit_data.get("committer") else None,
                        "id": commit_data.get("committer", {}).get("id") if commit_data.get("committer") else None,
                        "avatar_url": commit_data.get("committer", {}).get("avatar_url") if commit_data.get("committer") else None,
                        "gravatar_id": commit_data.get("committer", {}).get("gravatar_id") if commit_data.get("committer") else None,
                        "url": commit_data.get("committer", {}).get("url") if commit_data.get("committer") else None,
                        "html_url": commit_data.get("committer", {}).get("html_url") if commit_data.get("committer") else None,
                        "followers_url": commit_data.get("committer", {}).get("followers_url") if commit_data.get("committer") else None,
                        "following_url": commit_data.get("committer", {}).get("following_url") if commit_data.get("committer") else None,
                        "gists_url": commit_data.get("committer", {}).get("gists_url") if commit_data.get("committer") else None,
                        "starred_url": commit_data.get("committer", {}).get("starred_url") if commit_data.get("committer") else None,
                        "subscriptions_url": commit_data.get("committer", {}).get("subscriptions_url") if commit_data.get("committer") else None,
                        "organizations_url": commit_data.get("committer", {}).get("organizations_url") if commit_data.get("committer") else None,
                        "repos_url": commit_data.get("committer", {}).get("repos_url") if commit_data.get("committer") else None,
                        "events_url": commit_data.get("committer", {}).get("events_url") if commit_data.get("committer") else None,
                        "received_events_url": commit_data.get("committer", {}).get("received_events_url") if commit_data.get("committer") else None,
                        "type": commit_data.get("committer", {}).get("type") if commit_data.get("committer") else None,
                        "site_admin": commit_data.get("committer", {}).get("site_admin") if commit_data.get("committer") else None
                    }
                }
                processed_commits.append(commit_info)

            # Возвращаем результат в формате системы
            result = {
                "repository": {
                    "owner": owner,
                    "name": repo,
                    "branch": sha
                },
                "commits": processed_commits,
                "total_count": len(processed_commits),
                "full_response": commits  # Возвращаем полный ответ на случай, если понадобятся дополнительные данные
            }

            await logger.info(f"Successfully retrieved {len(processed_commits)} commits from {owner}/{repo}")
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP request error: {str(e)}"
                }
            }
        except httpx.TimeoutException as e:
            await logger.error(f"HTTP request timeout: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 408,
                    "description": f"Request timeout: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }