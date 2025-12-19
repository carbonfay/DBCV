"""Тесты для GitHub Create Pull Request интеграции."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.github.create_pull_request import GitHubCreatePullRequestIntegration, HTTPX_AVAILABLE
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


@pytest.fixture(scope="session", autouse=True)
async def engine():
    """Override heavy DB engine fixture to avoid the missing testing.postgresql dependency."""

    class _DummyBeginContext:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def run_sync(self, func):
            return None

    class _DummyEngine:
        async def begin(self):
            return _DummyBeginContext()

        async def connect(self):
            raise RuntimeError("Database access is not expected in GitHub integration tests")

        async def dispose(self):
            return None

    dummy_engine = _DummyEngine()
    yield dummy_engine
    await dummy_engine.dispose()


@pytest.fixture
def integration():
    return GitHubCreatePullRequestIntegration()


@pytest.fixture
def credentials_resolver():
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {"token": "ghp_test_token"}})
    resolver.get_by_id = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def logger():
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    return UUID("12345678-1234-5678-1234-567812345678")


def test_github_metadata(integration):
    metadata = integration.metadata

    assert metadata.id == "github_create_pull_request"
    assert metadata.version == "1.0.0"
    assert metadata.category == "github"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"
    assert metadata.library_name == "httpx"


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_success_minimal(integration, credentials_resolver, logger, bot_id):
    pr_payload = {
        "id": 1,
        "node_id": "MDExOlB1bGxSZXF1ZXN0MQ==",
        "number": 1,
        "title": "Add new feature",
        "state": "open",
        "locked": False,
        "draft": False,
        "user": {
            "id": 1,
            "login": "octocat",
            "type": "User",
            "html_url": "https://github.com/octocat",
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4"
        },
        "labels": [],
        "assignees": [],
        "requested_reviewers": [],
        "milestone": None,
        "body": None,
        "head": {
            "label": "octocat:feature-branch",
            "ref": "feature-branch",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
            "user": {
                "id": 1,
                "login": "octocat",
                "type": "User",
                "html_url": "https://github.com/octocat",
                "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4"
            },
            "repo": {
                "id": 1296269,
                "name": "Hello-World",
                "full_name": "octocat/Hello-World"
            }
        },
        "base": {
            "label": "octocat:main",
            "ref": "main",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
            "user": {
                "id": 1,
                "login": "octocat",
                "type": "User",
                "html_url": "https://github.com/octocat",
                "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4"
            },
            "repo": {
                "id": 1296269,
                "name": "Hello-World",
                "full_name": "octocat/Hello-World"
            }
        },
        "url": "https://api.github.com/repos/octocat/Hello-World/pulls/1",
        "html_url": "https://github.com/octocat/Hello-World/pull/1",
        "diff_url": "https://github.com/octocat/Hello-World/pull/1.diff",
        "patch_url": "https://github.com/octocat/Hello-World/pull/1.patch",
        "issue_url": "https://api.github.com/repos/octocat/Hello-World/issues/1",
        "commits_url": "https://api.github.com/repos/octocat/Hello-World/pulls/1/commits",
        "review_comments_url": "https://api.github.com/repos/octocat/Hello-World/pulls/1/comments",
        "review_comment_url": "https://api.github.com/repos/octocat/Hello-World/pulls/comments{/number}",
        "comments_url": "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
        "statuses_url": "https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e",
        "merged": False,
        "mergeable": True,
        "rebaseable": True,
        "mergeable_state": "clean",
        "merged_at": None,
        "merge_commit_sha": None,
        "comments": 0,
        "review_comments": 0,
        "maintainer_can_modify": False,
        "commits": 3,
        "additions": 100,
        "deletions": 3,
        "changed_files": 5,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "closed_at": None,
        "author_association": "OWNER"
    }

    create_response = MagicMock()
    create_response.status_code = 201
    create_response.json.return_value = pr_payload
    create_response.headers = {
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": "1700000000"
    }

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=create_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "title": "Add new feature",
                "head": "feature-branch",
                "base": "main"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    pr = result["response"]["result"]["pull_request"]
    assert pr["title"] == "Add new feature"
    assert pr["number"] == 1
    assert pr["repository"]["owner"] == "octocat"
    assert pr["repository"]["name"] == "Hello-World"
    assert pr["head"]["ref"] == "feature-branch"
    assert pr["base"]["ref"] == "main"
    assert result["response"]["result"]["rate_limit"]["limit"] == 5000
    mock_client.post.assert_awaited_once()


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_success_with_body(integration, credentials_resolver, logger, bot_id):
    pr_payload = {
        "id": 2,
        "number": 2,
        "title": "Fix bug",
        "state": "open",
        "locked": False,
        "draft": False,
        "user": {"id": 1, "login": "octocat", "type": "User", "html_url": "", "avatar_url": ""},
        "labels": [],
        "assignees": [],
        "requested_reviewers": [],
        "milestone": None,
        "body": "This PR fixes a critical bug.",
        "head": {
            "label": "octocat:fix-branch",
            "ref": "fix-branch",
            "sha": "abc123",
            "user": {"id": 1, "login": "octocat", "type": "User", "html_url": "", "avatar_url": ""},
            "repo": {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World"}
        },
        "base": {
            "label": "octocat:main",
            "ref": "main",
            "sha": "def456",
            "user": {"id": 1, "login": "octocat", "type": "User", "html_url": "", "avatar_url": ""},
            "repo": {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World"}
        },
        "url": "https://api.github.com/repos/octocat/Hello-World/pulls/2",
        "html_url": "https://github.com/octocat/Hello-World/pull/2",
        "diff_url": "https://github.com/octocat/Hello-World/pull/2.diff",
        "patch_url": "https://github.com/octocat/Hello-World/pull/2.patch",
        "issue_url": "https://api.github.com/repos/octocat/Hello-World/issues/2",
        "commits_url": "https://api.github.com/repos/octocat/Hello-World/pulls/2/commits",
        "review_comments_url": "https://api.github.com/repos/octocat/Hello-World/pulls/2/comments",
        "review_comment_url": "https://api.github.com/repos/octocat/Hello-World/pulls/comments{/number}",
        "comments_url": "https://api.github.com/repos/octocat/Hello-World/issues/2/comments",
        "statuses_url": "https://api.github.com/repos/octocat/Hello-World/statuses/abc123",
        "merged": False,
        "mergeable": True,
        "rebaseable": True,
        "mergeable_state": "clean",
        "merged_at": None,
        "merge_commit_sha": None,
        "comments": 0,
        "review_comments": 0,
        "maintainer_can_modify": False,
        "commits": 1,
        "additions": 10,
        "deletions": 5,
        "changed_files": 2,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "closed_at": None,
        "author_association": "OWNER"
    }

    create_response = MagicMock()
    create_response.status_code = 201
    create_response.json.return_value = pr_payload
    create_response.headers = {}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=create_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "title": "Fix bug",
                "head": "fix-branch",
                "base": "main",
                "body": "This PR fixes a critical bug."
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    pr = result["response"]["result"]["pull_request"]
    assert pr["title"] == "Fix bug"
    assert pr["body"] == "This PR fixes a critical bug."
    # Проверяем, что body был передан в запросе
    call_args = mock_client.post.call_args
    assert call_args[1]["json"]["body"] == "This PR fixes a critical bug."


@pytest.mark.asyncio
async def test_execute_no_credentials(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)
    resolver.get_by_id = AsyncMock(return_value=None)

    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "title": "Add feature",
            "head": "feature-branch",
            "base": "main"
        },
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_branch_not_found(integration, credentials_resolver, logger, bot_id):
    create_response = MagicMock()
    create_response.status_code = 422
    create_response.json.return_value = {
        "message": "Validation Failed",
        "errors": [
            {
                "resource": "PullRequest",
                "code": "invalid",
                "field": "head",
                "message": "head branch does not exist"
            }
        ]
    }
    create_response.headers = {}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=create_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "title": "Add feature",
                "head": "nonexistent-branch",
                "base": "main"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 422
    assert "Validation Failed" in result["response"]["description"]


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_repository_not_found(integration, credentials_resolver, logger, bot_id):
    create_response = MagicMock()
    create_response.status_code = 404
    create_response.json.return_value = {"message": "Not Found"}
    create_response.headers = {}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=create_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "nonexistent",
                "repo": "nonexistent",
                "title": "Add feature",
                "head": "feature-branch",
                "base": "main"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 404


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_with_credentials_id(integration, credentials_resolver, logger, bot_id):
    custom_cred_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    credentials_resolver.get_by_id.return_value = {"payload": {"token": "ghp_custom"}}

    pr_payload = {
        "id": 3,
        "number": 3,
        "title": "PR with explicit creds",
        "state": "open",
        "locked": False,
        "draft": False,
        "user": {"id": 3, "login": "user", "type": "User", "html_url": "", "avatar_url": ""},
        "labels": [],
        "assignees": [],
        "requested_reviewers": [],
        "milestone": None,
        "body": None,
        "head": {
            "label": "octocat:feature-branch",
            "ref": "feature-branch",
            "sha": "abc123",
            "user": {"id": 1, "login": "octocat", "type": "User", "html_url": "", "avatar_url": ""},
            "repo": {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World"}
        },
        "base": {
            "label": "octocat:main",
            "ref": "main",
            "sha": "def456",
            "user": {"id": 1, "login": "octocat", "type": "User", "html_url": "", "avatar_url": ""},
            "repo": {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World"}
        },
        "url": "https://api.github.com/repos/octocat/Hello-World/pulls/3",
        "html_url": "https://github.com/octocat/Hello-World/pull/3",
        "diff_url": "https://github.com/octocat/Hello-World/pull/3.diff",
        "patch_url": "https://github.com/octocat/Hello-World/pull/3.patch",
        "issue_url": "https://api.github.com/repos/octocat/Hello-World/issues/3",
        "commits_url": "https://api.github.com/repos/octocat/Hello-World/pulls/3/commits",
        "review_comments_url": "https://api.github.com/repos/octocat/Hello-World/pulls/3/comments",
        "review_comment_url": "https://api.github.com/repos/octocat/Hello-World/pulls/comments{/number}",
        "comments_url": "https://api.github.com/repos/octocat/Hello-World/issues/3/comments",
        "statuses_url": "https://api.github.com/repos/octocat/Hello-World/statuses/abc123",
        "merged": False,
        "mergeable": True,
        "rebaseable": True,
        "mergeable_state": "clean",
        "merged_at": None,
        "merge_commit_sha": None,
        "comments": 0,
        "review_comments": 0,
        "maintainer_can_modify": False,
        "commits": 1,
        "additions": 5,
        "deletions": 2,
        "changed_files": 1,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "closed_at": None,
        "author_association": "NONE"
    }

    create_response = MagicMock()
    create_response.status_code = 201
    create_response.json.return_value = pr_payload
    create_response.headers = {}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=create_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "title": "PR with explicit creds",
                "head": "feature-branch",
                "base": "main",
                "credentials_id": str(custom_cred_id)
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    credentials_resolver.get_by_id.assert_awaited_once_with(custom_cred_id)
    assert credentials_resolver.get_default_for.await_count == 0


@pytest.mark.asyncio
async def test_execute_invalid_credentials_id(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "title": "Add feature",
            "head": "feature-branch",
            "base": "main",
            "credentials_id": "invalid-uuid"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert credentials_resolver.get_by_id.await_count == 0
    assert credentials_resolver.get_default_for.await_count == 0


@pytest.mark.asyncio
async def test_execute_missing_owner(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={
            "repo": "Hello-World",
            "title": "Add feature",
            "head": "feature-branch",
            "base": "main"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "owner and repo are required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_execute_missing_repo(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={
            "owner": "octocat",
            "title": "Add feature",
            "head": "feature-branch",
            "base": "main"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "owner and repo are required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_execute_missing_title(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "head": "feature-branch",
            "base": "main"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "title is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_execute_missing_head(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "title": "Add feature",
            "base": "main"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "head is required" in result["response"]["description"]


@pytest.mark.asyncio
async def test_execute_missing_base(integration, credentials_resolver, logger, bot_id):
    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "title": "Add feature",
            "head": "feature-branch"
        },
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "base is required" in result["response"]["description"]


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_other_provider(integration, credentials_resolver, logger, bot_id):
    credentials_resolver.get_default_for = AsyncMock(return_value={"payload": {"token": "ghp_other"}})

    pr_payload = {
        "id": 4,
        "number": 4,
        "title": "PR with other provider",
        "state": "open",
        "locked": False,
        "draft": False,
        "user": {"id": 4, "login": "user", "type": "User", "html_url": "", "avatar_url": ""},
        "labels": [],
        "assignees": [],
        "requested_reviewers": [],
        "milestone": None,
        "body": None,
        "head": {
            "label": "octocat:feature-branch",
            "ref": "feature-branch",
            "sha": "abc123",
            "user": {"id": 1, "login": "octocat", "type": "User", "html_url": "", "avatar_url": ""},
            "repo": {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World"}
        },
        "base": {
            "label": "octocat:main",
            "ref": "main",
            "sha": "def456",
            "user": {"id": 1, "login": "octocat", "type": "User", "html_url": "", "avatar_url": ""},
            "repo": {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World"}
        },
        "url": "https://api.github.com/repos/octocat/Hello-World/pulls/4",
        "html_url": "https://github.com/octocat/Hello-World/pull/4",
        "diff_url": "https://github.com/octocat/Hello-World/pull/4.diff",
        "patch_url": "https://github.com/octocat/Hello-World/pull/4.patch",
        "issue_url": "https://api.github.com/repos/octocat/Hello-World/issues/4",
        "commits_url": "https://api.github.com/repos/octocat/Hello-World/pulls/4/commits",
        "review_comments_url": "https://api.github.com/repos/octocat/Hello-World/pulls/4/comments",
        "review_comment_url": "https://api.github.com/repos/octocat/Hello-World/pulls/comments{/number}",
        "comments_url": "https://api.github.com/repos/octocat/Hello-World/issues/4/comments",
        "statuses_url": "https://api.github.com/repos/octocat/Hello-World/statuses/abc123",
        "merged": False,
        "mergeable": True,
        "rebaseable": True,
        "mergeable_state": "clean",
        "merged_at": None,
        "merge_commit_sha": None,
        "comments": 0,
        "review_comments": 0,
        "maintainer_can_modify": False,
        "commits": 1,
        "additions": 5,
        "deletions": 2,
        "changed_files": 1,
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "closed_at": None,
        "author_association": "NONE"
    }

    create_response = MagicMock()
    create_response.status_code = 201
    create_response.json.return_value = pr_payload
    create_response.headers = {}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=create_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "title": "PR with other provider",
                "head": "feature-branch",
                "base": "main"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is True
    assert credentials_resolver.get_default_for.await_count == 1
    assert result["response"]["result"]["pull_request"]["number"] == 4


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_http_error(integration, credentials_resolver, logger, bot_id):
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=Exception("Connection error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "title": "Add feature",
                "head": "feature-branch",
                "base": "main"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] in [500, 502]


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx is required for this test")
@pytest.mark.asyncio
async def test_execute_invalid_json_response(integration, credentials_resolver, logger, bot_id):
    create_response = MagicMock()
    create_response.status_code = 201
    create_response.json.side_effect = ValueError("Invalid JSON")
    create_response.headers = {}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=create_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.integrations.github.create_pull_request.httpx.AsyncClient", return_value=mock_client):
        result = await integration.execute(
            config={
                "owner": "octocat",
                "repo": "Hello-World",
                "title": "Add feature",
                "head": "feature-branch",
                "base": "main"
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 500
    assert "Unable to parse" in result["response"]["description"]


@pytest.mark.asyncio
async def test_execute_no_token_in_credentials(integration, logger, bot_id):
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value={"payload": {}})
    resolver.get_by_id = AsyncMock(return_value=None)

    result = await integration.execute(
        config={
            "owner": "octocat",
            "repo": "Hello-World",
            "title": "Add feature",
            "head": "feature-branch",
            "base": "main"
        },
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "GitHub access token not found" in result["response"]["description"]
