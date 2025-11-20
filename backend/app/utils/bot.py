import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserModel
from app.models.bot import BotModel, BotVariables
from app.schemas import bot as schemas_bot
from uuid import UUID

from app.schemas.bot import BotExport
from app.schemas.message import MessagePrivateCreate
import app.crud.variables as crud_variables
import app.crud.message as crud_message

import app.crud.bot as crud_bot

logger = logging.getLogger(__name__)


def generate_unique_bot_name(original_name: str) -> str:
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{original_name}_{timestamp}"


async def import_bot_structure(session: AsyncSession, *, owner: UserModel, data: dict, target_bot_id: UUID = None) -> tuple[BotModel, bool]:
    bot_schema_all = schemas_bot.BotExport(**data, owner=owner)
    bot_in = schemas_bot.BotCreate(**data)
    
    original_name = bot_in.name
    unique_name = generate_unique_bot_name(original_name)
    bot_in.name = unique_name
    
    bot_schema_all.name = unique_name
    
    if target_bot_id:
        bot = await session.get(BotModel, target_bot_id)
        if not bot:
            raise ValueError(f"Bot with id {target_bot_id} not found")
        
        if bot.owner_id != owner.id:
            raise ValueError(f"User {owner.id} is not the owner of bot {target_bot_id}")

        new_first_step_id = None
        if bot_schema_all.first_step is not None:
            from app.schemas.step import StepCreate
            from app.crud.step import create_step
            new_first_step = await create_step(session, StepCreate(**bot_schema_all.first_step.model_dump(exclude={"bot_id"}), bot_id=target_bot_id))
            await session.commit()
            await session.refresh(new_first_step)
            new_first_step_id = new_first_step.id
            logger.info(f"Created new first step {new_first_step_id}")

        logger.info(f"Updating sessions for bot {target_bot_id} with new_step_id {new_first_step_id}")
        await update_sessions_step_id(session, target_bot_id, new_first_step_id)

        await delete_bot_structure(session, target_bot_id, exclude_step_ids=[new_first_step_id] if new_first_step_id else [])
        
        for key, value in bot_in.model_dump(exclude_unset=True).items():
            if hasattr(bot, key):
                setattr(bot, key, value)
        
        await session.commit()
        await session.refresh(bot)
        
        bot_variables = await crud_variables.get_variable_by_id(session, BotVariables, bot.id)
        bot_variables.data = bot_schema_all.variables.data
        await session.commit()
        await session.refresh(bot)
    else:
        bot = await crud_bot.create_bot(session, bot_in, owner)
        await session.commit()
        await session.refresh(bot)
        bot_variables = await crud_variables.get_variable_by_id(session, BotVariables, bot.id)

        bot_variables.data = bot_schema_all.variables.data
        await session.commit()
        await session.refresh(bot)

    # Create all steps bot's
    from app.schemas.step import StepCreate
    from app.crud.step import create_step
    steps = dict()
    
    if target_bot_id and new_first_step_id and bot_schema_all.first_step:
        from app.models import StepModel
        new_first_step = await session.get(StepModel, new_first_step_id)
        if new_first_step:
            steps[bot_schema_all.first_step.name] = new_first_step
    
    for step in bot_schema_all.steps:
        if step.name in steps:
            continue
            
        steps[step.name] = await create_step(session, StepCreate(**step.model_dump(exclude={"bot_id"}), bot_id=bot.id))
        await session.commit()
        await session.refresh(steps[step.name])
        if step.message is not None:
            steps[step.name].message = await crud_message.create_message(session,
                                                                         MessagePrivateCreate(**step.message.model_dump(
                                                                             exclude={"step_id"}),
                                                                                              step_id=steps[
                                                                                                  step.name].id),
                                                                         None)
        await session.commit()
        await session.refresh(steps[step.name])

    # Set first step bot
    if bot_schema_all.first_step is not None:
        first_step = steps[bot_schema_all.first_step.name]
        bot.first_step = first_step
        await session.commit()
        await session.refresh(first_step)
        await session.refresh(bot)

    # Create connection group
    from app.schemas.connection import ConnectionGroupCreate
    from app.schemas.connection import ConnectionCreate
    import app.crud.connection_group as crud_connection_group
    import app.crud.connection as crud_connection
    for step in bot_schema_all.steps:
        for connection_group_in in step.connection_groups:

            if connection_group_in.bot_id:
                break

            from app.schemas.request import RequestCreate
            from app.crud.request import create_request
            request_id = None
            if connection_group_in.request:
                request = await create_request(session, RequestCreate(**connection_group_in.request.dict()), owner_id=owner.id)
                await session.commit()
                await session.refresh(request)
                request_id = request.id
            connection_group = await crud_connection_group.create_connection_group(session, ConnectionGroupCreate(
                **connection_group_in.model_dump(exclude={"request_id", "step_id", "bot_id"}),
                step_id=steps[step.name].id,
                request_id=request_id,
            ))
            await session.commit()
            await session.refresh(connection_group)
            await session.refresh(steps[step.name])
            connections_in = connection_group_in.connections
            for connection_in in connections_in:
                connection = await crud_connection.create_connection(session, connection_group.id,
                                                                     ConnectionCreate(**connection_in.model_dump(
                                                                         exclude={"next_step_id", }),
                                                                                      next_step_id=steps[
                                                                                          connection_in.next_step.name].id))
                await session.commit()
                await session.refresh(connection)
                await session.refresh(connection_group)

    # Create master connection group
    for connection_group_in in bot_schema_all.master_connection_groups:
        from app.schemas.request import RequestCreate
        from app.crud.request import create_request
        request_id = None
        if connection_group_in.request:
            request = await create_request(session, RequestCreate(**connection_group_in.request.model_dump()), owner_id=owner.id)
            await session.commit()
            await session.refresh(request)
            request_id = request.id
        step_id = None
        if connection_group_in.step:
            step_id = steps[connection_group_in.step.name].id
        connection_group = await crud_connection_group.create_connection_group(session, ConnectionGroupCreate(
            **connection_group_in.model_dump(exclude={"request_id", "step_id", "bot_id"}),
            request_id=request_id,
            step_id=step_id,
            bot_id=bot.id,
        ))
        await session.commit()
        await session.refresh(connection_group)
        await session.refresh(bot)
        connections_in = connection_group_in.connections
        for connection_in in connections_in:
            next_step_id = None
            if connection_in.next_step:
                next_step_id = steps[connection_in.next_step.name].id
            connection = await crud_connection.create_connection(session, connection_group.id,
                                                                 ConnectionCreate(
                                                                     **connection_in.model_dump(
                                                                         exclude={"step_id", "next_step_id"}),
                                                                     next_step_id=next_step_id,
                                                                 ))
            await session.commit()
            await session.refresh(connection)
            await session.refresh(connection_group)
    return bot, target_bot_id is not None


async def delete_bot_structure(session: AsyncSession, bot_id: UUID, exclude_step_ids: list[UUID] = None) -> None:
    from app.models import StepModel, ConnectionGroupModel, ConnectionModel, MessageModel, RequestModel, NoteModel, EmitterModel, BotModel

    bot = await session.get(BotModel, bot_id)
    if bot and bot.first_step_id:
        bot.first_step_id = None
        await session.commit()

    messages = await session.execute(
        select(MessageModel).join(StepModel).where(StepModel.bot_id == bot_id)
    )
    for msg in messages.scalars():
        await session.delete(msg)

    request_ids_to_delete = set()
    
    connection_groups = await session.execute(
        select(ConnectionGroupModel).where(ConnectionGroupModel.bot_id == None).join(StepModel).where(StepModel.bot_id == bot_id)
    )
    for group in connection_groups.scalars():
        connections = await session.execute(
            select(ConnectionModel).where(ConnectionModel.group_id == group.id)
        )
        for conn in connections.scalars():
            await session.delete(conn)
        if group.request_id:
            request_ids_to_delete.add(group.request_id)
        await session.delete(group)

    master_groups = await session.execute(
        select(ConnectionGroupModel).where(ConnectionGroupModel.bot_id == bot_id)
    )
    for group in master_groups.scalars():
        connections = await session.execute(
            select(ConnectionModel).where(ConnectionModel.group_id == group.id)
        )
        for conn in connections.scalars():
            await session.delete(conn)
        if group.request_id:
            request_ids_to_delete.add(group.request_id)
        await session.delete(group)
    
    for request_id in request_ids_to_delete:
        request = await session.get(RequestModel, request_id)
        if request:
            await session.delete(request)

    notes = await session.execute(select(NoteModel).where(NoteModel.bot_id == bot_id))
    for note in notes.scalars():
        await session.delete(note)

    emitters = await session.execute(select(EmitterModel).where(EmitterModel.bot_id == bot_id))
    for emitter in emitters.scalars():
        await session.delete(emitter)

    exclude_step_ids = exclude_step_ids or []
    steps_query = select(StepModel).where(StepModel.bot_id == bot_id)
    if exclude_step_ids:
        steps_query = steps_query.where(StepModel.id.notin_(exclude_step_ids))
    
    steps = await session.execute(steps_query)
    for step in steps.scalars():
        logger.debug(f"Deleting step {step.id} (name: {step.name})")
        await session.delete(step)

    await session.commit()


async def update_sessions_step_id(session: AsyncSession, bot_id: UUID, new_step_id: UUID = None) -> None:
    """
    Обновляет step_id во всех сессиях бота на новый шаг.
    Если new_step_id = None, то удаляет сессии (так как step_id не может быть NULL).
    """
    from app.models import SessionModel
    from sqlalchemy import update, select
    
    sessions = await session.execute(
        select(SessionModel).where(SessionModel.bot_id == bot_id)
    )
    sessions_list = sessions.scalars().all()
    
    logger.info(f"Found {len(sessions_list)} sessions for bot {bot_id}")
    for sess in sessions_list:
        logger.debug(f"Session {sess.id} has step_id {sess.step_id}")
    
    if new_step_id is None:
        logger.info(f"No new step provided, deleting {len(sessions_list)} sessions")
        for sess in sessions_list:
            await session.delete(sess)
    else:
        result = await session.execute(
            update(SessionModel)
            .where(SessionModel.bot_id == bot_id)
            .values(step_id=new_step_id)
        )
        logger.info(f"Updated {result.rowcount} sessions to step_id {new_step_id}")
    
    await session.commit()


async def export_bot_structure(session: AsyncSession, bot: BotModel) -> dict:
    bot_data = bot.__dict__.copy()
    bot_data.pop("variables")
    variables = {"data": (await crud_variables.get_variable_by_id(session, BotVariables, bot.id)).data}
    bot_schema = schemas_bot.BotExport(**bot_data, variables=variables)
    return json.loads(bot_schema.model_dump_json(exclude={"owner", "owner_id"}))

from app.managers.data_manager import DataManager
from redis.asyncio import Redis
from app.config import settings
from app.database import sessionmanager


async def cache_structure_bot(session: AsyncSession, bot: BotModel) -> dict:
    export_json = await export_bot_structure(session, bot)
    bot.cache_structure = export_json
    await session.commit()

    redis = Redis.from_url(settings.CACHE_REDIS_URL)

    data_manager = DataManager(redis, sessionmanager.engine)
    await data_manager.update_bot(str(bot.id), export_json)


async def update_cache_variables_bot(bot: BotModel):
    redis = Redis.from_url(settings.CACHE_REDIS_URL)
    data_manager = DataManager(redis, sessionmanager.engine)
    await data_manager.update_bot_variables(str(bot.id), bot.variables.data)