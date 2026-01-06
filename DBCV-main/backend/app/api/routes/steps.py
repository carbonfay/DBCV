from typing import Annotated, Any, Optional, Union
from uuid import UUID
import json
import traceback

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
from app.managers.data_manager import DataManager
from app.loggers import BotLogger
from app.schemas.bot import BotProcessor
from app.engine.bot_processor import ConnectionHandlerFactory
from app.engine.variables import update_variables_dict
from app.auth.credentials_resolver import CredentialsResolver
from app.auth.service import AuthService
from app.utils.dict import deep_merge_dicts
from app.models.connection import SearchType

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
    response_model=schemas_step.StepExecuteOut,
)
async def run_step(
    step_id: Union[UUID, str],
    session: SessionDep,
    current_user: CurrentUser,
    step_in: schemas_step.StepExecuteIn,
) -> Any:
    """
    Выполняет все действия в шаге: проход по всем группам связей и выполнение действий
    (код, интеграции, HTTP-запросы) в порядке приоритета.
    """
    step = await crud_step.get_step(session, step_id, StepModel.default_eager_relationships)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)
    
    bot_id = step_in.bot_id or step.bot_id
    if not bot_id:
        raise HTTPException(status_code=400, detail="bot_id is required")
    
    dm = DataManager(Redis.from_url(settings.REDIS_URL), session.bind)
    logger = BotLogger(str(bot_id))
    logger.set_step(str(step_id))
    
    bot_data = await dm.get_bot(str(bot_id))
    if not bot_data:
        raise HTTPException(status_code=404, detail="Bot not found")
    bot = BotProcessor(**bot_data)
    
    step_export = schemas_step.StepExport.model_validate(step)
    
    sorted_groups = sorted(step_export.connection_groups, key=lambda g: g.priority)
    
    all_variables = step_in.variables.copy() if step_in.variables else {}
    context = step_in.context.copy() if step_in.context else {}
    
    merged_context = deep_merge_dicts(all_variables, context)
    
    resolver = CredentialsResolver(dm)
    auth_service = AuthService(resolver)
    
    results = []
    
    for group in sorted_groups:
        await logger.info(f"Processing connection group {group.id} (type: {group.search_type}, priority: {group.priority})...")
        
        handler = ConnectionHandlerFactory.get_handler(
            group.search_type,
            logger,
            bot=bot,
            auth=auth_service,
            data_manager=dm
        )
        
        if not handler:
            if group.search_type == SearchType.message:
                await logger.info("Skipping message type connection group")
                continue
            else:
                await logger.warning(f"No handler found for search_type: {group.search_type}")
                results.append(schemas_step.GroupExecutionResult(
                    group_id=str(group.id),
                    search_type=group.search_type.value,
                    priority=group.priority,
                    result=None,
                    variables_updated=None
                ))
                continue
        
        try:
            handler_result = await handler.handle(
                connection_group=group,
                context=merged_context,
                all_variables=all_variables
            )
            
            if handler_result is not None:
                merged_context = deep_merge_dicts(merged_context, handler_result)
                if isinstance(handler_result, dict):
                    context = deep_merge_dicts(context, handler_result)
            
            variables_before = all_variables.copy()
            if group.variables:
                try:
                    variables_save_as = group.variables
                    if isinstance(variables_save_as, str):
                        variables_save_as = json.loads(variables_save_as)
                    
                    all_variables = await update_variables_dict(
                        all_variables,
                        session, 
                        variables_save_as,
                        merged_context
                    )
                    
                    await logger.info("Variables updated in memory")
                except Exception as e:
                    await logger.error(f"Error saving variables: {e}")
            
            variables_updated = None
            if group.variables and all_variables != variables_before:
                variables_updated = {}
                for key in all_variables:
                    if key not in variables_before or all_variables[key] != variables_before.get(key):
                        variables_updated[key] = all_variables[key]
            
            results.append(schemas_step.GroupExecutionResult(
                group_id=str(group.id),
                search_type=group.search_type.value,
                priority=group.priority,
                result=handler_result,
                variables_updated=variables_updated
            ))
            
        except Exception as e:
            await logger.error(f"Error executing connection group {group.id}: {e}")
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"Traceback: {traceback_str}")
            
            results.append(schemas_step.GroupExecutionResult(
                group_id=str(group.id),
                search_type=group.search_type.value,
                priority=group.priority,
                result={"error": str(e), "traceback": traceback_str},
                variables_updated=None
            ))
    
    return schemas_step.StepExecuteOut(
        results=results,
        final_variables=all_variables
    )



