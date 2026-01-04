from typing import Annotated, Any, Union, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

import app.crud.step_execution_data as crud_step_execution_data
import app.crud.step as crud_step
import app.schemas.step_execution_data as schemas_step_execution_data
from app.api.dependencies.db import SessionDep
from app.models.access import AccessType
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser
from app.api.dependencies.auth import BotAccessChecker

router = APIRouter(prefix="/steps/{step_id}/execution-data", tags=["step-execution-data"])


@router.get(
    "/",
    response_model=Optional[schemas_step_execution_data.StepExecutionDataPublic],
)
async def get_step_execution_data_endpoint(
    step_id: Union[UUID, str],
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Получить сохраненные данные выполнения шага для текущего пользователя.
    
    Возвращает None, если данных еще нет (нормальная ситуация при первом открытии модального окна).
    """
    # Получаем шаг для проверки bot_id
    step = await crud_step.get_step(session, step_id)
    bot_id_for_access = step.bot_id
    if not bot_id_for_access:
        raise HTTPException(
            status_code=400, 
            detail="Step must have bot_id to check access"
        )
    # Используем _has_access_or_higher как в run_step
    await BotAccessChecker._has_access_or_higher(
        session, bot_id_for_access, current_user, AccessType.VIEWER
    )
    
    data = await crud_step_execution_data.get_step_execution_data(
        session, 
        step_id, 
        user_id=current_user.id
    )
    
    # Возвращаем None вместо 404 - это нормальная ситуация, когда данных еще нет
    return data if data else None


@router.put(
    "/",
    response_model=schemas_step_execution_data.StepExecutionDataPublic,
)
async def save_step_execution_data_endpoint(
    step_id: Union[UUID, str],
    session: SessionDep,
    current_user: CurrentUser,
    data_in: schemas_step_execution_data.StepExecutionDataUpdate,
) -> Any:
    """Сохранить данные выполнения шага для текущего пользователя"""
    # Получаем шаг для проверки bot_id
    step = await crud_step.get_step(session, step_id)
    bot_id_for_access = step.bot_id
    if not bot_id_for_access:
        raise HTTPException(
            status_code=400, 
            detail="Step must have bot_id to check access"
        )
    # Используем _has_access_or_higher как в run_step
    await BotAccessChecker._has_access_or_higher(
        session, bot_id_for_access, current_user, AccessType.VIEWER
    )
    
    data = await crud_step_execution_data.create_or_update_step_execution_data(
        session,
        step_id,
        data_in,
        user_id=current_user.id
    )
    
    await session.commit()
    await session.refresh(data)
    return data


@router.delete(
    "/",
    response_model=Message,
)
async def delete_step_execution_data_endpoint(
    step_id: Union[UUID, str],
    session: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """Удалить сохраненные данные выполнения шага для текущего пользователя"""
    # Получаем шаг для проверки bot_id
    step = await crud_step.get_step(session, step_id)
    bot_id_for_access = step.bot_id
    if not bot_id_for_access:
        raise HTTPException(
            status_code=400, 
            detail="Step must have bot_id to check access"
        )
    # Используем _has_access_or_higher как в run_step
    await BotAccessChecker._has_access_or_higher(
        session, bot_id_for_access, current_user, AccessType.VIEWER
    )
    
    await crud_step_execution_data.delete_step_execution_data(
        session,
        step_id,
        user_id=current_user.id
    )
    
    await session.commit()
    return Message(message="Execution data deleted successfully.")

