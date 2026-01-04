from __future__ import annotations

from typing import Annotated, Any, Union, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis

from app.api.dependencies.db import SessionDep
from app.api.dependencies.auth import CurrentBotEditor, CurrentBotViewer, CurrentBotOwner, CurrentUser
from app.schemas import credentials as schemas_cred
from app.crud import credentials as crud_cred
from app.crud.credentials_cache import invalidate_credential_cache
from app.config import settings
import logging

router = APIRouter(tags=["credentials"])


@router.get(
    "/",
    response_model=list[schemas_cred.CredentialListItem],
    dependencies=[CurrentBotViewer],
)
async def read_credentials(
    bot_id: Union[UUID, str],
    session: SessionDep
) -> Any:
    """
    Retrieve credentials for a bot (public meta, no payload).
    """
    items = await crud_cred.list_bot_credentials(session, bot_id)
    return items


@router.get(
    "/compatible",
    response_model=list[schemas_cred.CredentialListItem],
    dependencies=[CurrentBotViewer],
)
async def get_compatible_credentials(
    bot_id: Union[UUID, str],
    session: SessionDep,
    integration_id: Annotated[Optional[str], Query(description="Filter by integration ID")] = None,
    provider: Annotated[Optional[str], Query(description="Filter by provider")] = None,
    strategy: Annotated[Optional[str], Query(description="Filter by strategy")] = None,
) -> Any:
    """
    Получить список совместимых credentials для бота.
    
    Фильтрует credentials по совместимости с интеграцией или по provider/strategy.
    
    - Если указан `integration_id`: получает metadata интеграции и фильтрует по provider/strategy.
      Для интеграций с provider="other" возвращает все credentials бота.
    - Если указаны `provider` и/или `strategy`: фильтрует по указанным значениям.
    - Если ничего не указано: возвращает все credentials бота.
    
    Args:
        bot_id: ID бота
        integration_id: ID интеграции для фильтрации по совместимости
        provider: Provider для фильтрации
        strategy: Strategy для фильтрации
    
    Returns:
        Список совместимых credentials
    """
    items = await crud_cred.list_compatible_credentials(
        session,
        bot_id=bot_id,
        integration_id=integration_id,
        provider_hint=provider,
        strategy_hint=strategy
    )
    return items


@router.get(
    "/{cred_id}",
    response_model=schemas_cred.CredentialPublic,
    dependencies=[CurrentBotViewer],
)
async def read_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
) -> Any:
    """
    Get a specific credential by id (public meta, no payload).
    """
    cred = await crud_cred.get_credential(session, cred_id, bot_id=bot_id)
    return cred


@router.get(
    "/{cred_id}/payload",
    response_model=schemas_cred.CredentialPayloadResponse,
    dependencies=[CurrentBotOwner],
)
async def get_credential_payload(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get decrypted payload of a credential.
    
    **Security**: Only bot owner can access this endpoint. No exceptions.
    All access attempts are logged for audit purposes.
    """
    logger = logging.getLogger(__name__)
    
    # Получаем credential и проверяем принадлежность к боту
    cred = await crud_cred.get_credential(session, cred_id, bot_id=bot_id)
    
    # Логируем доступ к секретам
    logger.info(
        f"User {current_user.id} ({current_user.username}) accessed payload "
        f"for credential {cred_id} (bot_id={bot_id}, provider={cred.provider}, "
        f"strategy={cred.strategy})"
    )
    
    # Дешифруем payload
    from app.utils.secret_box import decrypt_blob_to_dict
    payload = decrypt_blob_to_dict(cred.data)
    
    return {"payload": payload}


@router.post(
    "/",
    response_model=schemas_cred.CredentialCreateOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[CurrentBotEditor],
)
async def create_credential(
    bot_id: Union[UUID, str],
    session: SessionDep,
    cred_in: schemas_cred.CredentialCreate,
) -> Any:
    """
    Create a credential for a bot (payload is encrypted before store).
    """
    if str(cred_in.bot_id) != str(bot_id):
        raise HTTPException(status_code=422, detail="bot_id mismatch with path")

    try:
        cred = await crud_cred.create_credential(session, cred_in)
        await session.commit()
        await session.refresh(cred)
        
        # Инвалидируем кэш после успешного commit
        redis = Redis.from_url(settings.CACHE_REDIS_URL)
        try:
            await invalidate_credential_cache(
                redis,
                str(cred_in.bot_id),
                cred_in.provider.value,
                cred_in.strategy.value
            )
        finally:
            await redis.aclose()
        
        return cred
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Integrity error: default constraint failed") from e


@router.patch(
    "/{cred_id}",
    response_model=schemas_cred.CredentialUpdateOut,
    dependencies=[CurrentBotEditor],
)
async def update_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
    cred_in: schemas_cred.CredentialUpdate,
) -> Any:
    """
    Update a credential (meta and/or payload). Enforces single default.
    """
    try:
        cred = await crud_cred.update_credential(session, cred_id, bot_id, cred_in)
        await session.commit()
        await session.refresh(cred)
        
        # Инвалидируем кэш после успешного commit
        redis = Redis.from_url(settings.CACHE_REDIS_URL)
        try:
            await invalidate_credential_cache(
                redis,
                str(cred.bot_id),
                cred.provider,
                cred.strategy
            )
        finally:
            await redis.aclose()
        
        return cred
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Integrity error: default constraint failed") from e


@router.post(
    "/{cred_id}/make-default",
    response_model=schemas_cred.CredentialPublic,
    dependencies=[CurrentBotEditor],
)
async def make_default_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
) -> Any:
    """
    Mark credential as default within (bot, provider, strategy).
    """
    cred = await crud_cred.get_credential(session, cred_id, bot_id=bot_id)
    cred.is_default = True
    await crud_cred._unset_other_defaults(
        session, bot_id=cred.bot_id, provider=cred.provider, strategy=cred.strategy, except_id=cred.id
    )
    await session.commit()
    await session.refresh(cred)
    
    # Инвалидируем кэш после успешного commit
    redis = Redis.from_url(settings.CACHE_REDIS_URL)
    try:
        await invalidate_credential_cache(
            redis,
            str(cred.bot_id),
            cred.provider,
            cred.strategy
        )
    finally:
        await redis.aclose()
    
    return cred


@router.delete(
    "/{cred_id}",
    dependencies=[CurrentBotEditor],
)
async def delete_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
) -> Any:
    """
    Delete a credential.
    """
    # Получаем credential перед удалением, чтобы знать provider и strategy для инвалидации кэша
    cred = await crud_cred.get_credential(session, cred_id, bot_id=bot_id)
    provider = cred.provider
    strategy = cred.strategy
    
    await crud_cred.delete_credential(session, cred_id, bot_id)
    await session.commit()
    
    # Инвалидируем кэш после успешного commit
    redis = Redis.from_url(settings.CACHE_REDIS_URL)
    try:
        await invalidate_credential_cache(
            redis,
            str(bot_id),
            provider,
            strategy
        )
    finally:
        await redis.aclose()
    
    return {"message": "Credential deleted successfully."}
