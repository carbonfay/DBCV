from typing import Annotated, Any, Optional, Union
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

import app.crud.step as crud_step
import app.crud.bot as crud_bot
import app.crud.channel as crud_channel
import app.crud.message as crud_message
import app.schemas.step as schemas_step
from app.api.dependencies.db import SessionDep
from app.api.routes.sockets import notify_channel
from app.models.step import StepModel
from app.models.access import AccessType
from app.schemas.message import Message, MessageCreate, MessagePublic
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentAdmin
from app.api.dependencies.auth import BotAccessChecker
from app.config import settings
from app.engine.bot_processor import ConnectionHandlerFactory
from app.loggers.bot import NoopBotLogger
from app.utils.dict import deep_merge_dicts, get_value_by_list_keys, deep_set
from app.managers.data_manager import DataManager
from app.auth.credentials_resolver import CredentialsResolver
from app.auth.service import AuthService
from app.schemas.bot import BotProcessor
from app.crud.step import validate_step_credential
from app.schemas import step as schemas_step_pkg
router = APIRouter()


@router.get(
    "/",
    response_model=list[schemas_step.StepPublic],
    dependencies=[CurrentAdmin]
)
async def read_steps(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve steps.
    """
    return await StepModel.get_all(session, skip, limit)


@router.post(
    "/",
    response_model=schemas_step.StepSimple,
)
async def create_step(session: SessionDep, current_user: CurrentUser, step_in: schemas_step.StepCreate) -> Any:
    """
    Create a step.
    """
    await BotAccessChecker._has_access(session, step_in.bot_id, current_user, AccessType.EDITOR)
    step = await crud_step.create_step(session, step_in)
    await session.commit()
    await session.refresh(step)
    return step


@router.patch(
    "/{step_id}",
    response_model=schemas_step.StepPublic,
)
async def update_step(
    step_id: Union[UUID, str], session: SessionDep,  current_user: CurrentUser, step_in: schemas_step.StepUpdate,
) -> Any:
    """
    Update a step.
    """
    await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)
    step = await crud_step.update_step(session, step_id, step_in)
    await session.commit()
    await session.refresh(step)
    return step


@router.delete("/{step_id}",
               response_model=Message)
async def delete_step(session: SessionDep, current_user: CurrentUser, step_id: Union[UUID, str]) -> Message:
    """
    Delete a step.
    """
    await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)
    await crud_step.delete_step(session, step_id)
    await session.commit()
    return Message(message="Step deleted successfully.")


@router.post(
    "/{step_id}/run",
    response_model=schemas_step.ExecuteStepOut,
)
async def run_step(
    step_id: Union[UUID, str],
    session: SessionDep,
    current_user: CurrentUser,
    request_in: schemas_step.ExecuteStepIn,
) -> Any:
    """
    Выполняет шаг с переданными переменными для тестирования/отладки.
    Выполняет все connection_groups шага и возвращает результаты.
    """
    # 1. Получить шаг с eager_relationships
    step = await crud_step.get_step(
        session, 
        step_id, 
        eager_relationships=StepModel.default_eager_relationships
    )
    
    # 2. Проверить доступ (используем _has_access_or_higher, чтобы EDITOR тоже проходил)
    bot_id_for_access = step.bot_id
    if not bot_id_for_access:
        raise HTTPException(
            status_code=400, 
            detail="Step must have bot_id to check access"
        )
    await BotAccessChecker._has_access_or_higher(
        session, bot_id_for_access, current_user, AccessType.VIEWER
    )
    
    # 3. Определить bot_id
    bot_id = request_in.bot_id or step.bot_id
    if not bot_id:
        raise HTTPException(
            status_code=400, 
            detail="bot_id is required (either in request or step.bot_id)"
        )

    # 3.1 Валидация разового credential для запуска (если указан)
    if request_in.credential_id:
        await validate_step_credential(
            session,
            credential_id=request_in.credential_id,
            bot_id=bot_id,
            step_id=step_id,
        )
    
    # 4. Преобразовать в StepExport
    step_export = schemas_step.StepExport.model_validate(step)

    # 4.1 Применяем временный credential_id для запуска (без сохранения в БД)
    if request_in.credential_id:
        step_export.credential_id = request_in.credential_id
        # Прокидываем в connection_groups -> step, чтобы StepAwareCredentialsResolver увидел override
        for cg in step_export.connection_groups or []:
            if cg.step:
                cg.step.credential_id = request_in.credential_id
            else:
                # Создаем минимальный StepSimple, если отсутствует
                cg.step = schemas_step_pkg.StepSimple(
                    id=step_export.id,
                    name=step_export.name,
                    is_proxy=step_export.is_proxy,
                    description=step_export.description,
                    bot_id=step_export.bot_id,
                    credential_id=request_in.credential_id,
                    template_instance_id=step_export.template_instance_id,
                    timeout_after=step_export.timeout_after,
                )
    
    # 5. Инициализировать зависимости
    dm = DataManager(Redis.from_url(settings.REDIS_URL), session.bind)
    bot = BotProcessor(**(await dm.get_bot(bot_id)))
    resolver = CredentialsResolver(dm)
    auth_service = AuthService(resolver)
    logger = NoopBotLogger()  # Не логируем в тестовом режиме
    
    # 6. Инициализировать переменные
    all_variables = request_in.variables.copy() if request_in.variables else {}
    context = request_in.variables.copy() if request_in.variables else {}
    
    # 7. Выполнить connection_groups
    connection_groups_results = []
    executed_count = 0
    success_count = 0
    error_count = 0
    
    for connection_group in step_export.connection_groups:
        executed_count += 1
        result_data = None
        error_msg = None
        variables_updated = {}
        
        try:
            # Получить handler
            handler = ConnectionHandlerFactory.get_handler(
                connection_group.search_type,
                logger,
                bot,
                auth_service,
                dm
            )
            
            if handler:
                # Выполнить handler
                result_data = await handler.handle(
                    connection_group,
                    context,
                    all_variables
                )
                
                # Обновить переменные в памяти (если указаны в connection_group.variables)
                if connection_group.variables:
                    variables_str = connection_group.variables
                    if isinstance(variables_str, str):
                        try:
                            variables_mapping = json.loads(variables_str)
                        except json.JSONDecodeError:
                            variables_mapping = {}
                    else:
                        variables_mapping = variables_str
                    
                    # Упрощённое обновление переменных в памяти (без сохранения в БД)
                    merged_context = deep_merge_dicts(all_variables, {"response": result_data} if result_data else {})
                    for source_path, target_path in variables_mapping.items():
                        # Простая логика: извлечь значение из merged_context по source_path
                        # и поместить в all_variables по target_path
                        value = get_value_by_list_keys(merged_context, source_path.split("."))
                        if value is not None:
                            deep_set(all_variables, target_path, value)
                            deep_set(variables_updated, target_path, value)
                
                # Обновить context для следующего connection_group
                if result_data:
                    context = deep_merge_dicts(context, {"response": result_data})
                
                success_count += 1
            else:
                error_msg = f"Handler not found for search_type: {connection_group.search_type}"
                error_count += 1
                
        except Exception as e:
            error_msg = str(e)
            error_count += 1
            await logger.error(f"Error executing connection_group {connection_group.id}: {e}")
        
        # Определить search_type как строку
        search_type_str = connection_group.search_type.value if hasattr(connection_group.search_type, 'value') else str(connection_group.search_type)
        
        connection_groups_results.append(
            schemas_step.ConnectionGroupResult(
                connection_group_id=connection_group.id,
                search_type=search_type_str,
                result=result_data,
                error=error_msg,
                variables_updated=variables_updated
            )
        )
    
    # 8. Вернуть результат
    return schemas_step.ExecuteStepOut(
        step_id=str(step_id),
        step_name=step.name,
        connection_groups_results=connection_groups_results,
        final_variables=all_variables,
        executed_count=executed_count,
        success_count=success_count,
        error_count=error_count
    )



