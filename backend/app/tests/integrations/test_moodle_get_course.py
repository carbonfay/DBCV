"""Тесты для интеграции Moodle Get Course."""
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.moodle.get_course import MoodleGetCourseIntegration
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Создает экземпляр интеграции Moodle Get Course."""
    return MoodleGetCourseIntegration()


@pytest.fixture
def credentials_resolver():
    """Создает mock для credentials resolver."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(
        return_value={
            "payload": {
                "base_url": "https://moodle.example",
                "token": "test-token",
            }
        }
    )
    return resolver


@pytest.fixture
def logger():
    """Создает mock логгера."""
    return MagicMock(spec=BotLogger)


@pytest.fixture
def bot_id():
    """Фиксированный bot_id для тестов."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_moodle_get_course_metadata(integration):
    """Проверяет базовые метаданные интеграции."""
    metadata = integration.metadata

    assert metadata.id == "moodle_get_course"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Moodle Get Course"
    assert metadata.category == "education"
    assert metadata.credentials_provider == "moodle"
    assert metadata.credentials_strategy == "api_key"
    assert "field" in metadata.config_schema.get("properties", {})
    assert "value" in metadata.config_schema.get("properties", {})


@pytest.mark.asyncio
async def test_moodle_get_course_success(integration, credentials_resolver, logger, bot_id):
    """Проверяет успешное получение курса по полю."""
    response_data = {"courses": [{"id": 7, "shortname": "course-7"}], "warnings": [{"warningcode": "test"}]}
    with patch(
        "app.integrations.moodle.get_course._fetch_moodle_json",
        new=AsyncMock(return_value=(response_data, None)),
    ) as mock_fetch:
        result = await integration.execute(
            config={"field": "shortname", "value": "course-7"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["course"] == {"id": 7, "shortname": "course-7"}
    assert result["response"]["result"]["warnings"] == [{"warningcode": "test"}]

    endpoint, params, _logger = mock_fetch.await_args.args
    assert endpoint == "https://moodle.example/webservice/rest/server.php"
    assert params["wsfunction"] == "core_course_get_courses_by_field"
    assert params["field"] == "shortname"
    assert params["value"] == "course-7"


@pytest.mark.asyncio
async def test_moodle_get_course_without_warnings(integration, credentials_resolver, logger, bot_id):
    """Проверяет, что warnings не возвращаются, если выключено include_warnings."""
    response_data = {"courses": [{"id": 3}]}
    with patch(
        "app.integrations.moodle.get_course._fetch_moodle_json",
        new=AsyncMock(return_value=(response_data, None)),
    ):
        result = await integration.execute(
            config={"field": "id", "value": "3", "include_warnings": False},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"]["course"] == {"id": 3}
    assert "warnings" not in result["response"]["result"]


@pytest.mark.asyncio
async def test_moodle_get_course_invalid_field(integration, credentials_resolver, logger, bot_id):
    """Проверяет ошибку при некорректном поле."""
    result = await integration.execute(
        config={"field": "unknown", "value": "x"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_moodle_get_course_no_credentials(integration, logger, bot_id):
    """Проверяет ошибку при отсутствии credentials."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(return_value=None)

    result = await integration.execute(
        config={"field": "id", "value": "1"},
        credentials_resolver=resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
