"""GitHub Create Pull Request интеграция используя PyGithub библиотеку."""
from typing import Dict, Any, TYPE_CHECKING, Optional, List
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata

if TYPE_CHECKING:
    from app.auth.credentials_resolver import CredentialsResolver
    from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    from github import Github
    from github.GithubException import GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    Github = None
    GithubException = Exception


class GitHubCreatePullRequestIntegration(BaseIntegration):
    """Интеграция для создания Pull Request на GitHub (POST /repos/{owner}/{repo}/pulls)."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_create_pull_request",
            version="1.0.0",
            name="GitHub Create Pull Request",
            description="Создание нового Pull Request на GitHub с заголовком, описанием и указанием веток",
            category="integration",
            icon_s3_key="icons/integrations/github.svg",
            color="#ffffff",
            config_schema={
                "type": "object",
                "required": ["owner", "repo", "title", "head", "base"],
                "properties": {
                    "owner": {
                        "type": "string",
                        "title": "Repository Owner",
                        "description": "Владелец репозитория (username или организация)"
                    },
                    "repo": {
                        "type": "string",
                        "title": "Repository Name",
                        "description": "Название репозитория"
                    },
                    "title": {
                        "type": "string",
                        "title": "Pull Request Title",
                        "description": "Название Pull Request"
                    },
                    "head": {
                        "type": "string",
                        "title": "Head Branch",
                        "description": "Ветка с изменениями (например: 'feature/new-feature' или 'username:feature-branch')"
                    },
                    "base": {
                        "type": "string",
                        "title": "Base Branch",
                        "description": "Целевая ветка для merge (например: 'main' или 'develop')"
                    },
                    "body": {
                        "type": "string",
                        "title": "Pull Request Body",
                        "description": "Описание Pull Request (опционально)"
                    },
                    "draft": {
                        "type": "boolean",
                        "title": "Draft",
                        "description": "Создать как draft PR (опционально, по умолчанию false)"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "Labels",
                        "description": "Список labels для PR (опционально)"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "Assignees",
                        "description": "Список username для assignees (опционально)"
                    },
                    "reviewers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "title": "Reviewers",
                        "description": "Список username для request reviewers (опционально)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="none",
            library_name="PyGithub>=2.0.0" if GITHUB_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать простой Pull Request",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "title": "Add new feature",
                        "head": "feature/new-feature",
                        "base": "main",
                        "body": "This PR adds new functionality to the system"
                    }
                },
                {
                    "title": "Создать Draft PR с reviewers и labels",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "title": "Work in progress: database optimization",
                        "head": "dev:database-optimization",
                        "base": "main",
                        "body": "Work in progress on database optimization",
                        "draft": True,
                        "labels": ["enhancement", "database"],
                        "reviewers": ["user1", "user2"],
                        "assignees": ["user1"]
                    }
                },
                {
                    "title": "Создать PR из fork",
                    "config": {
                        "owner": "carbonfay",
                        "repo": "DBCV",
                        "title": "Fix typo in documentation",
                        "head": "external-contributor:fix-typo",
                        "base": "main"
                    }
                }
            ]
        )
    
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: "CredentialsResolver",
        bot_id: UUID,
        logger: "BotLogger"
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию создания Pull Request используя библиотеку PyGithub.
        
        Args:
            config: Параметры интеграции (owner, repo, title, head, base и опциональные параметры)
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not GITHUB_AVAILABLE:
            await logger.error("PyGithub library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "PyGithub library is not installed"
                }
            }
        
        # Получаем token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )
        
        if not creds:
            await logger.error("GitHub credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "GitHub token not found in credentials"
                }
            }
        
        # Credentials возвращаются с ключом "payload"
        payload = creds.get("payload", {})
        if not payload:
            payload = creds
        
        token = payload.get("token") or payload.get("access_token")
        if not token:
            await logger.error(f"token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "token not found in credentials"
                }
            }
        
        # Получаем обязательные параметры из config
        owner = config.get("owner", "").strip()
        repo = config.get("repo", "").strip()
        title = config.get("title", "").strip()
        head = config.get("head", "").strip()
        base = config.get("base", "").strip()
        
        # Валидация обязательных параметров
        if not owner or not repo or not title or not head or not base:
            await logger.error("owner, repo, title, head and base are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "owner, repo, title, head and base are required"
                }
            }
        
        # Получаем опциональные параметры
        body = config.get("body", "").strip() or None
        draft = config.get("draft", False)
        labels = config.get("labels", [])
        assignees = config.get("assignees", [])
        reviewers = config.get("reviewers", [])
        
        # Валидация типов опциональных параметров
        if not isinstance(draft, bool):
            await logger.error("draft must be a boolean")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "draft must be a boolean"
                }
            }
        
        if not isinstance(labels, list):
            await logger.error("labels must be a list")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "labels must be a list"
                }
            }
        
        if not isinstance(assignees, list):
            await logger.error("assignees must be a list")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "assignees must be a list"
                }
            }
        
        if not isinstance(reviewers, list):
            await logger.error("reviewers must be a list")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "reviewers must be a list"
                }
            }
        
        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем Github клиент с access token
            g = Github(token)
            
            # Получаем репозиторий
            repo_obj = g.get_user(owner).get_repo(repo)
            
            # Создаем Pull Request
            pr = repo_obj.create_pull(
                title=title,
                head=head,
                base=base,
                body=body,
                draft=draft
            )
            
            # Добавляем labels если указаны
            if labels:
                try:
                    pr.add_to_labels(*labels)
                except GithubException as e:
                    await logger.warning(f"Failed to add labels to PR: {e}")
                    # Продолжаем выполнение, labels - не критичны
            
            # Добавляем assignees если указаны
            if assignees:
                try:
                    pr.add_to_assignees(*assignees)
                except GithubException as e:
                    await logger.warning(f"Failed to add assignees to PR: {e}")
                    # Продолжаем выполнение, assignees - не критичны
            
            # Добавляем reviewers если указаны
            if reviewers:
                try:
                    pr.create_review_request(reviewers=reviewers)
                except GithubException as e:
                    await logger.warning(f"Failed to add reviewers to PR: {e}")
                    # Продолжаем выполнение, reviewers - не критичны
            
            # Переполучаем обновленный PR для получения полной информации
            updated_pr = repo_obj.get_pull(pr.number)
            
            # Формируем результат с информацией о созданном PR
            result = {
                "id": updated_pr.id,
                "number": updated_pr.number,
                "title": updated_pr.title,
                "body": updated_pr.body,
                "state": updated_pr.state,
                "draft": updated_pr.draft,
                "user": {
                    "login": updated_pr.user.login,
                    "id": updated_pr.user.id,
                    "avatar_url": updated_pr.user.avatar_url,
                    "url": updated_pr.user.html_url
                },
                "head": {
                    "ref": updated_pr.head.ref,
                    "sha": updated_pr.head.sha,
                    "repo": {
                        "name": updated_pr.head.repo.name if updated_pr.head.repo else None,
                        "full_name": updated_pr.head.repo.full_name if updated_pr.head.repo else None,
                        "url": updated_pr.head.repo.html_url if updated_pr.head.repo else None
                    }
                },
                "base": {
                    "ref": updated_pr.base.ref,
                    "sha": updated_pr.base.sha,
                    "repo": {
                        "name": updated_pr.base.repo.name,
                        "full_name": updated_pr.base.repo.full_name,
                        "url": updated_pr.base.repo.html_url
                    }
                },
                "created_at": updated_pr.created_at.isoformat() if updated_pr.created_at else None,
                "updated_at": updated_pr.updated_at.isoformat() if updated_pr.updated_at else None,
                "closed_at": updated_pr.closed_at.isoformat() if updated_pr.closed_at else None,
                "merged_at": updated_pr.merged_at.isoformat() if updated_pr.merged_at else None,
                "labels": [label.name for label in updated_pr.labels],
                "assignees": [assignee.login for assignee in updated_pr.assignees],
                "comments": updated_pr.comments,
                "commits": updated_pr.commits,
                "additions": updated_pr.additions,
                "deletions": updated_pr.deletions,
                "changed_files": updated_pr.changed_files,
                "url": updated_pr.html_url,
                "api_url": updated_pr.url
            }
            
            await logger.debug(f"Successfully created PR #{updated_pr.number} in {owner}/{repo}")
            
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }
        
        except GithubException as e:
            error_msg = e.data.get("message", str(e)) if hasattr(e, 'data') else str(e)
            await logger.error(f"GitHub API error: {e.status if hasattr(e, 'status') else 'Unknown'} - {error_msg}")
            return {
                "response": {
                    "ok": False,
                    "error_code": getattr(e, 'status', 500),
                    "description": f"GitHub API error: {error_msg}"
                }
            }
        
        except Exception as e:
            await logger.error(f"Unexpected error: {str(e)}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Unexpected error: {str(e)}"
                }
            }
