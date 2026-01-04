from __future__ import annotations

from typing import Type, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credentials import CredentialEntity
from app.schemas import credentials as schemas_cred
from app.utils.secret_box import encrypt_dict_to_blob


async def _raise_not_found() -> None:
    raise HTTPException(status_code=404, detail="Credential not found.")


async def get_credential(session: AsyncSession, cred_id: UUID | str,
                         *, bot_id: UUID | str | None = None) -> Type[CredentialEntity]:
    stmt = select(CredentialEntity).where(CredentialEntity.id == cred_id)
    if bot_id:
        stmt = stmt.where(CredentialEntity.bot_id == bot_id)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if not row:
        await _raise_not_found()
    return row  # type: ignore


async def list_bot_credentials(session: AsyncSession, bot_id: UUID | str) -> list[CredentialEntity]:
    stmt = (
        select(CredentialEntity)
        .where(CredentialEntity.bot_id == bot_id)
        .order_by(CredentialEntity.provider, CredentialEntity.strategy, CredentialEntity.name)
    )
    return list((await session.execute(stmt)).scalars().all())


async def _unset_other_defaults(session: AsyncSession,
                                *,
                                bot_id: UUID | str,
                                provider: str,
                                strategy: str,
                                except_id: UUID | str | None = None) -> None:
    stmt = (
        update(CredentialEntity)
        .where(
            CredentialEntity.bot_id == bot_id,
            CredentialEntity.provider == provider,
            CredentialEntity.strategy == strategy,
            CredentialEntity.is_default.is_(True),
        )
        .values(is_default=False, updated_at=func.now())
    )
    if except_id:
        stmt = stmt.where(CredentialEntity.id != except_id)
    await session.execute(stmt)


async def create_credential(
    session: AsyncSession,
    cred_in: schemas_cred.CredentialCreate,
) -> CredentialEntity:
    db_obj = CredentialEntity(
        bot_id=cred_in.bot_id,
        name=cred_in.name,
        provider=cred_in.provider.value,
        strategy=cred_in.strategy.value,
        scopes=cred_in.scopes,
        data=encrypt_dict_to_blob(cred_in.payload),
        is_default=cred_in.is_default,
    )
    session.add(db_obj)
    await session.flush()

    if cred_in.is_default:
        await _unset_other_defaults(
            session,
            bot_id=cred_in.bot_id,
            provider=cred_in.provider.value,
            strategy=cred_in.strategy.value,
            except_id=db_obj.id,
        )
    
    return db_obj


async def update_credential(
    session: AsyncSession,
    cred_id: UUID | str,
    bot_id: UUID | str,
    cred_in: schemas_cred.CredentialUpdate,
) -> CredentialEntity:
    cred = await get_credential(session, cred_id, bot_id=bot_id)

    if cred_in.name is not None:
        cred.name = cred_in.name
    if cred_in.scopes is not None:
        cred.scopes = cred_in.scopes
    if cred_in.payload is not None:
        cred.data = encrypt_dict_to_blob(cred_in.payload)

    if cred_in.is_default is not None:
        cred.is_default = cred_in.is_default
        if cred_in.is_default:
            await _unset_other_defaults(
                session,
                bot_id=cred.bot_id,
                provider=cred.provider,
                strategy=cred.strategy,
                except_id=cred.id,
            )

    return cred


async def delete_credential(session: AsyncSession, cred_id: UUID | str, bot_id: UUID | str) -> None:
    cred = await get_credential(session, cred_id, bot_id=bot_id)
    await session.delete(cred)


async def list_compatible_credentials(
    session: AsyncSession,
    bot_id: UUID | str,
    integration_id: Optional[str] = None,
    provider_hint: Optional[str] = None,
    strategy_hint: Optional[str] = None
) -> list[CredentialEntity]:
    """
    Получает список совместимых credentials для бота.
    
    Args:
        session: Сессия БД
        bot_id: ID бота
        integration_id: ID интеграции (опционально) - если указан, фильтрует по provider/strategy интеграции
        provider_hint: Provider для фильтрации (опционально)
        strategy_hint: Strategy для фильтрации (опционально)
    
    Returns:
        Список совместимых credentials
    """
    # Получаем все credentials бота
    all_credentials = await list_bot_credentials(session, bot_id)
    
    # Определяем provider и strategy для фильтрации
    provider = provider_hint
    strategy = strategy_hint
    
    # Если указан integration_id, получаем metadata интеграции
    if integration_id:
        from app.integrations.registry import registry
        integration = registry.get(integration_id)
        if integration:
            metadata = integration.metadata
            # Для provider="other" возвращаем все credentials бота
            if metadata.credentials_provider == "other":
                return all_credentials
            # Для provider != "other" фильтруем по совместимости
            provider = metadata.credentials_provider
            strategy = metadata.credentials_strategy
            
            # Если интеграция имеет strategy="other", показываем все credentials с тем же provider
            # Это позволяет использовать любой credential с этим provider для интеграций, которые не требуют конкретного типа credentials
            if strategy == "other":
                # Возвращаем все credentials с указанным provider независимо от их strategy
                return [c for c in all_credentials if c.provider == provider]
        else:
            # Интеграция не найдена - возвращаем пустой список
            return []
    
    # Фильтруем по provider и strategy (если указаны)
    filtered = all_credentials
    if provider:
        filtered = [c for c in filtered if c.provider == provider]
    if strategy and strategy != "other":
        filtered = [c for c in filtered if c.strategy == strategy]
    
    return filtered