from typing import Dict, Any
from uuid import UUID
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

try:
    from github import Github
    from github.GithubException import GithubException
    PYGITHUB_AVAILABLE = True
except Exception:
    Github = None
    GithubException = Exception
    PYGITHUB_AVAILABLE = False

class GitHubGetRepositoryIntegration(BaseIntegration):
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="github_get_repository",
            version="1.0.0",
            name="GitHub Get Repository",
            description="Получить информацию о репозитории GitHub",
            category="developer_tools",
            icon_s3_key="icons/integrations/github.svg",
            color="#24292e",
            config_schema={
                "type": "object",
                "required": ["full_name"],
                "properties": {
                    "full_name": {"type": "string", "title": "Repository Full Name"}
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="PyGithub>=1.55" if PYGITHUB_AVAILABLE else None
        )

    async def execute(self, config: Dict[str, Any], credentials_resolver: CredentialsResolver, bot_id: UUID, logger: BotLogger) -> Dict[str, Any]:
        if not PYGITHUB_AVAILABLE:
            return {"response": {"ok": False, "description": "PyGithub not installed"}}

        full_name = config.get("full_name")
        if not full_name:
            return {"response": {"ok": False, "description": "full_name is required"}}

        creds = await credentials_resolver.get_default_for(bot_id=bot_id, provider="other", strategy="api_key")
        if not creds:
            return {"response": {"ok": False, "description": "GitHub credentials not found"}}

        payload = creds.get("payload", {}) if isinstance(creds, dict) else creds
        token = payload.get("api_key") or payload.get("access_token") if isinstance(payload, dict) else creds

        try:
            gh = Github(token)
            repo = gh.get_repo(full_name)
            return {
                "response": {
                    "ok": True, 
                    "result": {"id": repo.id, "full_name": repo.full_name, "stars": repo.stargazers_count}
                }
            }
        except Exception as e:
            return {"response": {"ok": False, "description": str(e)}}