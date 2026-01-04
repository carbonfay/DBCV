from typing import Type, List, Sequence, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models import StepModel
from app.models.step import StepModel
from app.models.connection import ConnectionGroupModel
from app.schemas import step as schemas_step
from app.crud.utils import is_object_unique
from app.crud.message import create_message
from app.crud.bot import get_bot
from app.crud.credentials import get_credential
from app.integrations.registry import registry


async def check_step_unique(
        session: AsyncSession,
        step_in: schemas_step.StepBase,
        exclude_id: UUID | str | None = None,
) -> None:
    if not await is_step_unique(session, step_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The step with the given name already exists.",
        )


async def is_step_unique(
        session: AsyncSession,
        step_in: schemas_step.StepBase | schemas_step.StepUpdate,
        exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        StepModel,
        step_in,
        unique_fields=("name",),
        exclude_id=exclude_id,
    )


async def get_step(session: AsyncSession, step_id: UUID | str,
                   eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[StepModel]:
    step = await StepModel.get_obj(session, step_id, eager_relationships)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found.")
    return step


async def create_step(
        session: AsyncSession, step_in: schemas_step.StepCreate,
) -> StepModel:
    # Валидация credential перед созданием
    await validate_step_credential(
        session,
        credential_id=step_in.credential_id,
        bot_id=step_in.bot_id
    )
    
    db_obj = StepModel(
        **step_in.model_dump(),
    )
    session.add(db_obj)
    await session.flush()  # Получаем ID шага для валидации с интеграциями
    
    # Повторная валидация с учетом connection_groups (если они уже есть)
    # Но при создании шага connection_groups обычно еще нет, поэтому эта проверка будет пустой
    await validate_step_credential(
        session,
        credential_id=step_in.credential_id,
        bot_id=step_in.bot_id,
        step_id=db_obj.id
    )
    
    return db_obj


async def update_step(
        session: AsyncSession,
        step_id: UUID | str,
        step_in: schemas_step.StepUpdate,
) -> Type[StepModel]:
    step = await get_step(session, step_id)
    
    # Определяем bot_id для валидации (из запроса или из существующего шага)
    bot_id = step_in.bot_id if step_in.bot_id is not None else step.bot_id
    if not bot_id:
        raise HTTPException(
            status_code=400,
            detail="bot_id is required for credential validation"
        )
    
    # Получаем обновленные данные (включая credential_id, если он установлен)
    updated_data = step_in.model_dump(exclude_unset=True)
    
    # Валидация credential перед обновлением (если credential_id изменяется)
    if 'credential_id' in updated_data:
        credential_id = updated_data.get('credential_id')
        await validate_step_credential(
            session,
            credential_id=credential_id,
            bot_id=bot_id,
            step_id=step_id
        )
    
    for key, value in updated_data.items():
        setattr(step, key, value)
    return step


async def delete_step(session: AsyncSession, step_id: UUID | str) -> None:
    await session.delete(await get_step(session, step_id))


async def get_steps_by_bot(session: AsyncSession, bot_id: UUID | str) -> Sequence[StepModel]:
    return (
        await session.scalars(select(StepModel).where(getattr(StepModel, "bot_id") == bot_id))
    ).fetchall()


async def validate_step_credential(
    session: AsyncSession,
    credential_id: Optional[UUID | str],
    bot_id: UUID | str,
    step_id: Optional[UUID | str] = None
) -> None:
    """
    Валидирует credential для шага.
    
    Проверяет:
    1. Существование credential
    2. Принадлежность credential к боту шага
    3. Совместимость provider/strategy с интеграциями шага (если есть connection_groups с интеграциями)
    
    Args:
        session: Сессия БД
        credential_id: ID credential для проверки (может быть None)
        bot_id: ID бота шага
        step_id: ID шага (опционально, для проверки совместимости с интеграциями)
    
    Raises:
        HTTPException: Если валидация не пройдена
    """
    if not credential_id:
        return  # Нет credential_id - валидация не требуется
    
    # 1. Проверка существования credential и принадлежности к боту
    try:
        credential = await get_credential(session, credential_id, bot_id=bot_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Credential {credential_id} not found or does not belong to bot {bot_id}"
            )
        raise
    
    # 2. Если указан step_id, проверяем совместимость с интеграциями
    if step_id:
        # Получаем connection_groups шага с интеграциями
        stmt = (
            select(ConnectionGroupModel)
            .where(
                ConnectionGroupModel.step_id == step_id,
                ConnectionGroupModel.integration_id.isnot(None)
            )
        )
        connection_groups = (await session.execute(stmt)).scalars().all()
        
        # Проверяем совместимость credential с каждой интеграцией
        for connection_group in connection_groups:
            if not connection_group.integration_id:
                continue
            
            integration = registry.get(connection_group.integration_id)
            if not integration:
                continue  # Интеграция не найдена, пропускаем
            
            metadata = integration.metadata
            
            # Для provider="other" валидация совместимости не выполняется
            if metadata.credentials_provider == "other":
                continue
            
            # Проверяем совместимость provider
            if credential.provider != metadata.credentials_provider:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Credential {credential_id} is not compatible with integration "
                        f"{connection_group.integration_id}. "
                        f"Expected provider={metadata.credentials_provider}, "
                        f"but got provider={credential.provider}"
                    )
                )
            
            # Если интеграция имеет strategy="other", принимаем любой credential с тем же provider
            # Если strategy != "other", проверяем строгое совпадение strategy
            if metadata.credentials_strategy != "other":
                if credential.strategy != metadata.credentials_strategy:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Credential {credential_id} is not compatible with integration "
                            f"{connection_group.integration_id}. "
                            f"Expected provider={metadata.credentials_provider}, strategy={metadata.credentials_strategy}, "
                            f"but got provider={credential.provider}, strategy={credential.strategy}"
                        )
                    )

