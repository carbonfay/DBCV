"""Tests for Medicine Get Clinical Trials integration."""
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.credentials_resolver import CredentialsResolver
from app.integrations.medicine.get_trials import MedicineGetTrialsIntegration
from app.loggers.bot import BotLogger


@pytest.fixture
def integration():
    """Create Medicine Get Clinical Trials integration instance."""
    return MedicineGetTrialsIntegration()


@pytest.fixture
def credentials_resolver():
    """Create credentials resolver mock."""
    resolver = MagicMock(spec=CredentialsResolver)
    resolver.get_default_for = AsyncMock(
        return_value={
            "payload": {
                "api_key": "test-key",
                "api_key_header": "X-API-Key",
            }
        }
    )
    return resolver


@pytest.fixture
def logger():
    """Create bot logger mock with async error handler."""
    mock_logger = MagicMock(spec=BotLogger)
    mock_logger.error = AsyncMock()
    return mock_logger


@pytest.fixture
def bot_id():
    """Fixed bot_id for tests."""
    return UUID("12345678-1234-5678-1234-567812345678")


def test_trials_metadata(integration):
    """Validate metadata values."""
    metadata = integration.metadata

    assert metadata.id == "medicine_get_trials"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Medicine Get Clinical Trials"
    assert metadata.category == "medicine"
    assert metadata.credentials_provider == "medicine"
    assert metadata.credentials_strategy == "api_key"


@pytest.mark.asyncio
async def test_trials_execute_success(integration, credentials_resolver, logger, bot_id):
    """Verify successful execution and parameter mapping."""
    expected_data = {"items": [{"id": "trial-1"}]}
    with patch(
        "app.integrations.medicine.get_trials._fetch_trials",
        new=AsyncMock(return_value=(expected_data, None)),
    ) as mock_fetch:
        result = await integration.execute(
            config={
                "base_url": "https://medicine.example.com",
                "query": "diabetes",
                "condition": "diabetes",
                "status": "recruiting",
                "page": 2,
                "page_size": 25,
                "params": {"extra": "value"},
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    assert result["response"]["result"] == expected_data

    endpoint, headers, params, _logger = mock_fetch.await_args.args
    assert endpoint == "https://medicine.example.com/api/v1/trials"
    assert headers == {"X-API-Key": "test-key"}
    assert params["query"] == "diabetes"
    assert params["condition"] == "diabetes"
    assert params["status"] == "recruiting"
    assert params["page"] == 2
    assert params["page_size"] == 25
    assert params["extra"] == "value"


@pytest.mark.asyncio
async def test_trials_execute_fhir_source_defaults(integration, credentials_resolver, logger, bot_id):
    """Verify default endpoint for FHIR source."""
    with patch(
        "app.integrations.medicine.get_trials._fetch_trials",
        new=AsyncMock(return_value=({"entry": []}, None)),
    ) as mock_fetch:
        result = await integration.execute(
            config={
                "source": "fhir",
                "base_url": "https://hapi.fhir.org/baseR4",
                "condition": "diabetes",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    endpoint, _headers, params, _logger = mock_fetch.await_args.args
    assert endpoint == "https://hapi.fhir.org/baseR4/ResearchStudy"
    assert params["condition"] == "diabetes"


@pytest.mark.asyncio
async def test_trials_execute_medlineplus_query_mapping(integration, credentials_resolver, logger, bot_id):
    """Verify MedlinePlus query mapping and default response type."""
    with patch(
        "app.integrations.medicine.get_trials._fetch_trials",
        new=AsyncMock(return_value=({"feed": []}, None)),
    ) as mock_fetch:
        result = await integration.execute(
            config={
                "source": "medlineplus",
                "base_url": "https://connect.medlineplus.gov",
                "query": "asthma",
            },
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger,
        )

    assert result["response"]["ok"] is True
    endpoint, _headers, params, _logger = mock_fetch.await_args.args
    assert endpoint == "https://connect.medlineplus.gov/service"
    assert params["mainSearchCriteria.v.dn"] == "asthma"
    assert params["knowledgeResponseType"] == "application/json"


@pytest.mark.asyncio
async def test_trials_execute_invalid_base_url(integration, credentials_resolver, logger, bot_id):
    """Verify invalid base_url returns error response."""
    result = await integration.execute(
        config={"base_url": "not-a-url"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400


@pytest.mark.asyncio
async def test_trials_execute_invalid_params_type(integration, credentials_resolver, logger, bot_id):
    """Verify params must be a dict."""
    result = await integration.execute(
        config={"base_url": "https://medicine.example.com", "params": "bad"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger,
    )

    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
