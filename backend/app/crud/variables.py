import json
import logging
from uuid import UUID

from app.models import BotVariables
from app.models import UserVariables
from app.models import AnonymousUserVariables
from app.models import ChannelVariables
from app.models import SessionVariables
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import sessionmanager
from redis.asyncio import Redis
from app.managers.data_manager import DataManager


async def _invalidate_variables_cache(variable_id: str, cls_variables):
    """Инвалидирует кеш переменных в зависимости от типа"""
    try:
        redis = Redis.from_url(settings.CACHE_REDIS_URL)
        data_manager = DataManager(redis, sessionmanager.engine)
        
        if cls_variables == UserVariables:
            await data_manager.invalidate_user_variables_cache(variable_id)
        elif cls_variables == BotVariables:
            await data_manager.invalidate_bot_variables_cache(variable_id)
        elif cls_variables == ChannelVariables:
            await data_manager.invalidate_channel_variables_cache(variable_id)
        elif cls_variables == SessionVariables:
            await data_manager.invalidate_session_variables_cache(variable_id)
        
        await redis.aclose()
    except Exception as e:
        logging.warning(f"Failed to invalidate cache for {cls_variables.__name__}:{variable_id}: {e}")


async def get_variable_by_id(session: AsyncSession,
                             cls_variables: BotVariables | UserVariables | ChannelVariables | SessionVariables,
                             variable_id: UUID | str):
    variable_obj = await session.get(cls_variables, variable_id)
    if variable_obj is None and cls_variables == UserVariables:
        variable_obj = await session.get(AnonymousUserVariables, variable_id)
    if isinstance(variable_obj.data, str):
        variable_obj.data = json.loads(variable_obj.data)
    return variable_obj


async def get_variable_by_pks(session: AsyncSession,
                              cls_variables: BotVariables | UserVariables | ChannelVariables | SessionVariables,
                              variable_pks: tuple[str]):
    variable_obj = await session.get(cls_variables, variable_pks)

    if variable_obj is None and cls_variables == UserVariables:
        variable_obj = await session.get(AnonymousUserVariables, variable_pks)
    if variable_obj is None:
        return None
    if isinstance(variable_obj.data, str):
        variable_obj.data = json.loads(variable_obj.data)
    return variable_obj


async def update_variable_by_id(session: AsyncSession,
                                cls_variables: BotVariables | UserVariables | ChannelVariables | SessionVariables,
                                variable_id: UUID | str,
                                variables: dict):
    variable_obj = await get_variable_by_id(session, cls_variables, variable_id)
    if isinstance(variable_obj.data, str):
        variable_obj.data = json.loads(variable_obj.data)

    data = variables if variable_obj.data is None else {**variable_obj.data, **variables}
    setattr(variable_obj, "data", data)
    
    # Инвалидируем кеш после обновления
    await _invalidate_variables_cache(str(variable_id), cls_variables)
    
    return variable_obj


async def full_update_variable_by_id(session: AsyncSession,
                                    cls_variables: BotVariables | UserVariables | ChannelVariables | SessionVariables,
                                    variable_id: UUID | str,
                                    variables: dict):
    variable_obj = await get_variable_by_id(session, cls_variables, variable_id)
    setattr(variable_obj, "data", variables)
    
    # Инвалидируем кеш после обновления
    await _invalidate_variables_cache(str(variable_id), cls_variables)
    
    return variable_obj


async def update_variable_by_pks(session: AsyncSession,
                                 cls_variables: BotVariables | UserVariables | ChannelVariables | SessionVariables,
                                 variable_pks: tuple[str],
                                 variables: dict):

    variable_obj = await get_variable_by_pks(session, cls_variables, variable_pks)
    if variable_obj is None:
        return None
    if isinstance(variable_obj.data, str):
        variable_obj.data = json.loads(variable_obj.data)
    data = variables if variable_obj.data is None else {**variable_obj.data, **variables}
    setattr(variable_obj, "data", data)
    
    await _invalidate_variables_cache(str(variable_pks[0]), cls_variables)
    
    return variable_obj




