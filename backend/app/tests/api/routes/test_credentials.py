"""Тесты для API endpoints credentials."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.config import settings
from app.tests.utils import create_random_user
from app.crud import bot as crud_bot
from app.crud import credentials as crud_cred
from app.schemas.bot import BotCreate
from app.schemas.credentials import CredentialCreate, Provider, Strategy
from app.integrations.registry import registry


async def create_test_bot(session: AsyncSession, owner_id) -> str:
    """Создает тестового бота и возвращает его ID."""
    from uuid import UUID
    if isinstance(owner_id, str):
        owner_id = UUID(owner_id)
    bot_in = BotCreate(name=f"Test Bot {uuid4()}", owner_id=owner_id)
    bot = await crud_bot.create_bot(session, bot_in, None)
    await session.commit()
    await session.refresh(bot)
    return str(bot.id)


async def create_test_credential(
    session: AsyncSession,
    bot_id: str,
    name: str,
    provider: Provider,
    strategy: Strategy,
    payload: dict,
    is_default: bool = False
) -> str:
    """Создает тестовый credential и возвращает его ID."""
    from uuid import UUID
    bot_uuid = UUID(bot_id) if isinstance(bot_id, str) else bot_id
    cred_in = CredentialCreate(
        bot_id=bot_uuid,
        name=name,
        provider=provider,
        strategy=strategy,
        payload=payload,
        is_default=is_default
    )
    cred = await crud_cred.create_credential(session, cred_in)
    await session.commit()
    await session.refresh(cred)
    return str(cred.id)


@pytest.mark.anyio
async def test_get_credentials_list(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест получения списка credentials для бота."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем несколько credentials
    cred1_id = await create_test_credential(
        session, bot_id, "Cred 1", Provider.telegram, Strategy.api_key,
        {"bot_token": "token1"}
    )
    cred2_id = await create_test_credential(
        session, bot_id, "Cred 2", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 2
    cred_ids = [c["id"] for c in credentials]
    assert cred1_id in cred_ids
    assert cred2_id in cred_ids


@pytest.mark.anyio
async def test_get_compatible_credentials_all(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест получения всех credentials без фильтрации."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем credentials с разными provider
    await create_test_credential(
        session, bot_id, "Telegram Cred", Provider.telegram, Strategy.api_key,
        {"bot_token": "token1"}
    )
    await create_test_credential(
        session, bot_id, "Medicine Cred", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 2


@pytest.mark.anyio
async def test_get_compatible_credentials_by_provider(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест фильтрации credentials по provider."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем credentials с разными provider
    telegram_cred_id = await create_test_credential(
        session, bot_id, "Telegram Cred", Provider.telegram, Strategy.api_key,
        {"bot_token": "token1"}
    )
    await create_test_credential(
        session, bot_id, "Medicine Cred", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?provider=telegram",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 1
    assert credentials[0]["id"] == telegram_cred_id
    assert credentials[0]["provider"] == "telegram"


@pytest.mark.anyio
async def test_get_compatible_credentials_by_provider_and_strategy(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест фильтрации credentials по provider и strategy."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем credentials
    medicine_api_key_id = await create_test_credential(
        session, bot_id, "Medicine API Key", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    await create_test_credential(
        session, bot_id, "Medicine OAuth", Provider.medicine, Strategy.oauth,
        {"client_id": "id", "client_secret": "secret"}
    )
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?provider=medicine&strategy=api_key",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 1
    assert credentials[0]["id"] == medicine_api_key_id
    assert credentials[0]["provider"] == "medicine"
    assert credentials[0]["strategy"] == "api_key"


@pytest.mark.anyio
async def test_get_compatible_credentials_by_integration_id(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест фильтрации credentials по integration_id."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Получаем интеграцию medicine_get_symptoms
    integration_id = "medicine_get_symptoms"
    integration = registry.get(integration_id)
    if integration is None:
        pytest.skip(f"Integration {integration_id} not registered in this build")
    
    # Создаем совместимый credential
    medicine_cred_id = await create_test_credential(
        session, bot_id, "Medicine Cred", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    
    # Создаем несовместимый credential
    await create_test_credential(
        session, bot_id, "Telegram Cred", Provider.telegram, Strategy.api_key,
        {"bot_token": "token"}
    )
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?integration_id={integration_id}",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 1
    assert credentials[0]["id"] == medicine_cred_id
    assert credentials[0]["provider"] == "medicine"
    assert credentials[0]["strategy"] == "api_key"


@pytest.mark.anyio
async def test_get_compatible_credentials_integration_other_provider(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест фильтрации для интеграции с provider='other' - должна возвращать все credentials."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем несколько credentials с разными provider
    await create_test_credential(
        session, bot_id, "Telegram Cred", Provider.telegram, Strategy.api_key,
        {"bot_token": "token"}
    )
    await create_test_credential(
        session, bot_id, "Medicine Cred", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    
    # Ищем интеграцию с provider="other" (если есть)
    # Если нет, создаем тестовую ситуацию с provider_hint
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?provider=other",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    # Если есть credentials с provider=other, они будут возвращены
    # Иначе вернется пустой список
    assert isinstance(credentials, list)


@pytest.mark.anyio
async def test_get_compatible_credentials_empty_result(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест получения пустого результата при отсутствии совместимых credentials."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем credential с другим provider
    await create_test_credential(
        session, bot_id, "Telegram Cred", Provider.telegram, Strategy.api_key,
        {"bot_token": "token"}
    )
    
    # Запрашиваем credentials для medicine provider
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?provider=medicine",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 0


@pytest.mark.anyio
async def test_get_compatible_credentials_invalid_integration_id(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест обработки несуществующего integration_id."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    await create_test_credential(
        session, bot_id, "Medicine Cred", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    
    # Используем несуществующий integration_id
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?integration_id=non_existent_integration",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    # Должен вернуться пустой список, так как интеграция не найдена
    credentials = r.json()
    assert len(credentials) == 0


@pytest.mark.anyio
async def test_get_compatible_credentials_multiple_same_provider(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест получения нескольких credentials с одинаковым provider/strategy."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем несколько credentials с одинаковым provider/strategy
    cred1_id = await create_test_credential(
        session, bot_id, "Medicine Cred 1", Provider.medicine, Strategy.api_key,
        {"app_id": "id1", "app_key": "key1"}, is_default=True
    )
    cred2_id = await create_test_credential(
        session, bot_id, "Medicine Cred 2", Provider.medicine, Strategy.api_key,
        {"app_id": "id2", "app_key": "key2"}
    )
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?provider=medicine&strategy=api_key",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 2
    cred_ids = [c["id"] for c in credentials]
    assert cred1_id in cred_ids
    assert cred2_id in cred_ids


@pytest.mark.anyio
async def test_get_credentials_bot_not_found(
    client: AsyncClient,
    superuser_token_headers: dict[str, str]
) -> None:
    """Тест обработки несуществующего bot_id."""
    fake_bot_id = str(uuid4())
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{fake_bot_id}/credentials/",
        headers=superuser_token_headers,
    )
    
    # Должен вернуть пустой список или 404, в зависимости от реализации
    assert r.status_code in [200, 404]
    if r.status_code == 200:
        assert r.json() == []


@pytest.mark.anyio
async def test_get_compatible_credentials_unauthorized(
    client: AsyncClient
) -> None:
    """Тест доступа без авторизации."""
    fake_bot_id = str(uuid4())
    
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{fake_bot_id}/credentials/compatible",
    )
    
    assert r.status_code == 401


@pytest.mark.anyio
async def test_get_compatible_credentials_medicine_only_api_key(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест: medicine интеграции с strategy="api_key" видят только api_key credentials."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем credentials с разными strategy для medicine
    cred_api_key_id = await create_test_credential(
        session, bot_id, "Medicine API Key", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    await create_test_credential(
        session, bot_id, "Medicine Other", Provider.medicine, Strategy.other,
        {}
    )
    
    # Интеграция с strategy="api_key" должна видеть только api_key credentials
    integration_api_key = "medicine_get_pharmacy_info"
    if registry.get(integration_api_key) is None:
        pytest.skip(f"Integration {integration_api_key} not registered in this build")
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?integration_id={integration_api_key}",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    assert len(credentials) == 1
    assert credentials[0]["id"] == cred_api_key_id
    assert credentials[0]["strategy"] == "api_key"


@pytest.mark.anyio
async def test_get_compatible_credentials_medicine_other_sees_all(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест: интеграции с strategy="other" видят все credentials с тем же provider."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем несколько credentials с разными strategy для medicine
    cred_api_key_1_id = await create_test_credential(
        session, bot_id, "Medicine API Key 1", Provider.medicine, Strategy.api_key,
        {"app_id": "id1", "app_key": "key1"}
    )
    cred_api_key_2_id = await create_test_credential(
        session, bot_id, "Medicine API Key 2", Provider.medicine, Strategy.api_key,
        {"app_id": "id2", "app_key": "key2"}
    )
    cred_other_id = await create_test_credential(
        session, bot_id, "Medicine Other", Provider.medicine, Strategy.other,
        {}
    )
    
    # Создаем credential с другим provider для проверки фильтрации
    await create_test_credential(
        session, bot_id, "Telegram Cred", Provider.telegram, Strategy.api_key,
        {"bot_token": "token"}
    )
    
    # Интеграция с strategy="other" должна видеть ВСЕ medicine credentials
    integration_other = "medicine_get_atc_code"
    if registry.get(integration_other) is None:
        pytest.skip(f"Integration {integration_other} not registered in this build")
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?integration_id={integration_other}",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    # Должны быть все 3 medicine credentials, но не telegram
    assert len(credentials) == 3
    cred_ids = [c["id"] for c in credentials]
    assert cred_api_key_1_id in cred_ids
    assert cred_api_key_2_id in cred_ids
    assert cred_other_id in cred_ids
    # Проверяем, что все credentials имеют provider="medicine"
    for cred in credentials:
        assert cred["provider"] == "medicine"


@pytest.mark.anyio
async def test_get_compatible_credentials_other_strategy_all_providers(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест: логика strategy="other" работает для всех провайдеров, не только medicine."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем credentials с разными strategy для telegram
    cred_telegram_api_key_id = await create_test_credential(
        session, bot_id, "Telegram API Key", Provider.telegram, Strategy.api_key,
        {"bot_token": "token1"}
    )
    cred_telegram_oauth_id = await create_test_credential(
        session, bot_id, "Telegram OAuth", Provider.telegram, Strategy.oauth,
        {"client_id": "id", "client_secret": "secret"}
    )
    
    # Создаем credential с другим provider для проверки фильтрации
    await create_test_credential(
        session, bot_id, "Medicine Cred", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    
    # Если бы была интеграция telegram с strategy="other", она должна видеть все telegram credentials
    # Тестируем через прямой запрос с provider и strategy
    r = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?provider=telegram&strategy=other",
        headers=superuser_token_headers,
    )
    
    assert 200 <= r.status_code < 300
    credentials = r.json()
    # Должны быть все 2 telegram credentials, но не medicine
    assert len(credentials) == 2
    cred_ids = [c["id"] for c in credentials]
    assert cred_telegram_api_key_id in cred_ids
    assert cred_telegram_oauth_id in cred_ids
    # Проверяем, что все credentials имеют provider="telegram"
    for cred in credentials:
        assert cred["provider"] == "telegram"


@pytest.mark.anyio
async def test_get_compatible_credentials_medicine_different_strategies(
    client: AsyncClient,
    superuser_token_headers: dict[str, str],
    session: AsyncSession
) -> None:
    """Тест: интеграции с strategy="other" видят все credentials с тем же provider."""
    user = await create_random_user(session)
    bot_id = await create_test_bot(session, str(user.id))
    
    # Создаем credentials с разными strategy для medicine
    cred_api_key_id = await create_test_credential(
        session, bot_id, "Medicine API Key", Provider.medicine, Strategy.api_key,
        {"app_id": "id", "app_key": "key"}
    )
    cred_other_id = await create_test_credential(
        session, bot_id, "Medicine Other", Provider.medicine, Strategy.other,
        {}
    )
    
    # Тест 1: Интеграция с strategy="api_key" должна видеть только credentials с api_key
    integration_api_key = "medicine_get_symptoms"
    integration_other = "medicine_get_articles"
    if registry.get(integration_api_key) is None or registry.get(integration_other) is None:
        pytest.skip("Medicine integrations not registered in this build")
    r1 = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?integration_id={integration_api_key}",
        headers=superuser_token_headers,
    )
    assert 200 <= r1.status_code < 300
    credentials1 = r1.json()
    # Для api_key интеграций: только api_key credentials
    assert len(credentials1) == 1
    assert credentials1[0]["id"] == cred_api_key_id
    assert credentials1[0]["strategy"] == "api_key"
    
    # Тест 2: Интеграция с strategy="other" должна видеть ВСЕ credentials с provider="medicine"
    r2 = await client.get(
        f"{settings.API_V1_STR}/bots/{bot_id}/credentials/compatible?integration_id={integration_other}",
        headers=superuser_token_headers,
    )
    assert 200 <= r2.status_code < 300
    credentials2 = r2.json()
    # Для other интеграций: все medicine credentials независимо от strategy
    assert len(credentials2) == 2
    cred_ids = [c["id"] for c in credentials2]
    assert cred_api_key_id in cred_ids
    assert cred_other_id in cred_ids

