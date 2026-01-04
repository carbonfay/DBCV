from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.step_execution_data import StepExecutionDataModel
import app.schemas.step_execution_data as schemas_step_execution_data


async def get_step_execution_data(
    session: AsyncSession, 
    step_id: UUID | str,
    user_id: Optional[UUID | str] = None
) -> Optional[StepExecutionDataModel]:
    """Получить сохраненные данные выполнения шага для конкретного пользователя"""
    query = select(StepExecutionDataModel).where(
        StepExecutionDataModel.step_id == step_id
    )
    
    if user_id:
        query = query.where(StepExecutionDataModel.user_id == user_id)
    else:
        query = query.where(StepExecutionDataModel.user_id.is_(None))
    
    return (await session.execute(query)).scalar_one_or_none()


async def create_or_update_step_execution_data(
    session: AsyncSession,
    step_id: UUID | str,
    data_in: schemas_step_execution_data.StepExecutionDataCreate | schemas_step_execution_data.StepExecutionDataUpdate,
    user_id: Optional[UUID | str] = None
) -> StepExecutionDataModel:
    """Создать или обновить сохраненные данные выполнения шага (upsert)"""
    existing = await get_step_execution_data(session, step_id, user_id)
    
    if existing:
        # Обновляем существующую запись
        for key, value in data_in.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        return existing
    else:
        # Создаем новую запись
        db_obj = StepExecutionDataModel(
            step_id=step_id,
            user_id=user_id,
            **data_in.model_dump(exclude_unset=True)
        )
        session.add(db_obj)
        return db_obj


async def delete_step_execution_data(
    session: AsyncSession,
    step_id: UUID | str,
    user_id: Optional[UUID | str] = None
) -> None:
    """Удалить сохраненные данные выполнения шага"""
    data = await get_step_execution_data(session, step_id, user_id)
    if data:
        await session.delete(data)

