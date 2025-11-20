"""Тесты для базовых классов интеграций."""
import pytest
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class TestIntegration(BaseIntegration):
    """Тестовая интеграция."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="test_integration",
            version="1.0.0",
            name="Test Integration",
            description="Test",
            category="test",
            icon_s3_key="icons/test.svg",
            color="#000000",
            config_schema={"type": "object"},
            credentials_provider="test",
            credentials_strategy="api_key"
        )
    
    async def execute(self, config, credentials_resolver, bot_id, logger):
        return {"response": {"ok": True, "result": {"test": "data"}}}


@pytest.mark.asyncio
async def test_base_integration_metadata():
    """Тест получения метаданных интеграции."""
    integration = TestIntegration()
    metadata = integration.metadata
    
    assert metadata.id == "test_integration"
    assert metadata.version == "1.0.0"
    assert metadata.name == "Test Integration"
    assert metadata.category == "test"


@pytest.mark.asyncio
async def test_base_integration_execute():
    """Тест выполнения интеграции."""
    integration = TestIntegration()
    credentials_resolver = MagicMock(spec=CredentialsResolver)
    logger = MagicMock(spec=BotLogger)
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    result = await integration.execute(
        config={"test": "config"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result == {"response": {"ok": True, "result": {"test": "data"}}}

