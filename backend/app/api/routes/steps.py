from typing import Annotated, Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from fastapi.responses import JSONResponse

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
from app.managers.data_manager import DataManager
from app.config import settings
from redis.asyncio import Redis
from app.database import sessionmanager
from app.models.bot import BotModel

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


from pydantic import BaseModel

class RunStepRequest(BaseModel):
    integration_config: dict = {}

@router.post("/{step_id}/run", response_model=dict)
async def run_step(
    step_id: Union[UUID, str],
    request: RunStepRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Run a step manually.
    """
    # Получаем шаг
    step = await session.get(StepModel, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    # Проверяем доступ к боту
    await BotAccessChecker._has_access(session, step.bot_id, current_user, AccessType.EDITOR)

    # Подготовим данные для выполнения интеграции
    redis = Redis.from_url(settings.CACHE_REDIS_URL)
    data_manager = DataManager(redis, sessionmanager.engine)

    # Используем BotLogger
    from app.loggers.bot import BotLogger
    logger = BotLogger(step.bot_id)

    # Ищем интеграцию в connection_groups шага
    from app.schemas.connection import ConnectionGroupExport
    from app.engine.integration_handler import ConnectionIntegrationHandler

    # Проходим по всем connection_groups шага
    for connection_group in step.connection_groups:
        if connection_group.search_type == "integration":
            # Создаем копию connection_group с обновленной конфигурацией, если она передана
            import copy
            connection_group_dict = connection_group.__dict__.copy()
            # Удаляем служебные атрибуты SQLAlchemy
            connection_group_dict = {k: v for k, v in connection_group_dict.items() if not k.startswith('_sa_')}

            if request.integration_config:
                # Обновляем конфигурацию интеграции
                connection_group_dict["integration_config"] = request.integration_config

            connection_group_export = ConnectionGroupExport.model_validate(connection_group_dict)

            # Создаем handler для интеграции
            handler = ConnectionIntegrationHandler(logger, data_manager, step.bot_id)

            try:
                # Подготовим контекст с переменными пользователя
                # Включим в контекст информацию о пользователе и боте
                context = {
                    "step_id": str(step_id),
                    "user_id": str(current_user.id),
                    "user": {
                        "id": str(current_user.id),
                        "username": current_user.username,
                        "telegram_chat_id": getattr(current_user, 'telegram_chat_id', None)  # если поле существует
                    },
                    "bot_id": str(step.bot_id)
                }

                # Выполняем интеграцию
                result = await handler.handle(
                    connection_group=connection_group_export,
                    context=context,
                    all_variables={}
                )

                if result:
                    return {
                        "status": "success",
                        "step_id": str(step_id),
                        "integration_result": result
                    }
                else:
                    return {
                        "status": "integration_no_result",
                        "step_id": str(step_id)
                    }
            except Exception as e:
                await logger.error(f"Error executing integration in step {step_id}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error executing integration: {str(e)}")

    # Если не найдено интеграций для выполнения
    raise HTTPException(status_code=400, detail="No integration found in step connection groups")

