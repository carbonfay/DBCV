from __future__ import annotations

from typing import Type
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credentials import CredentialEntity
from app.schemas import credentials as schemas_cred
from app.utils.secret_box import encrypt_dict_to_blob


async def _raise_not_found() -> None:
    raise HTTPException(status_code=404, detail="Credential not found.")


async def _invalidate_credential_cache(bot_id: str, provider: str, strategy: str) -> None:
    """Инвалидирует кэш credentials для указанного bot_id, provider и strategy."""
    from redis.asyncio import Redis
    from app.config import settings
    try:
        redis = Redis.from_url(settings.CACHE_REDIS_URL)
        # Удаляем конкретные ключи кэша
        await redis.delete(
            f"credential:bot:{bot_id}:provider:{provider}:strategy:{strategy}:default",
            f"credential:bot:{bot_id}:provider:{provider}:strategy:{strategy}:singleton"
        )
        await redis.aclose()
    except Exception:
        pass  # Игнорируем ошибки кэша


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
    
    # Инвалидируем кэш credentials после создания
    await _invalidate_credential_cache(str(cred_in.bot_id), cred_in.provider.value, cred_in.strategy.value)
    
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
    
    # Инвалидируем кэш credentials после обновления
    await _invalidate_credential_cache(str(cred.bot_id), cred.provider, cred.strategy)

    return cred


async def delete_credential(session: AsyncSession, cred_id: UUID | str, bot_id: UUID | str) -> None:
    cred = await get_credential(session, cred_id, bot_id=bot_id)
    provider = cred.provider
    strategy = cred.strategy
    await session.delete(cred)
    
    # Инвалидируем кэш credentials после удаления
    await _invalidate_credential_cache(str(bot_id), provider, strategy)