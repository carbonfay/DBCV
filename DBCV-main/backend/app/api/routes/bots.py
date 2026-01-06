import os
from typing import Annotated, Any, Union, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, UploadFile, File, Body
from sqlalchemy import select, insert
import json
import app.crud.bot as crud_bot
import app.crud.user as crud_user
import app.schemas.bot as schemas_bot
import app.schemas.step as schemas_step
from app.api.dependencies.db import SessionDep
from app.models import UserModel
from app.models.bot import BotModel
from app.schemas.message import Message, MessagePrivateCreate
from app.api.dependencies.auth import CurrentUser, CurrentDeveloperDep, CurrentBotEditor, CurrentBotViewer, \
    BotAccessChecker
from app.models.role import RoleType
from app.models.access import AccessType
from app.models.user_bot_access import user_bot_access
from uuid import UUID
from app.utils.files import create_temp_json_file
from fastapi.responses import FileResponse, JSONResponse
import app.crud.variables as crud_variables
import app.crud.message as crud_message
import app.crud.step as crud_step
from app.models.bot import BotVariables

from app.utils.bot import export_bot_structure, import_bot_structure, delete_bot_structure, cache_structure_bot, \
    update_cache_variables_bot


router = APIRouter()


@router.get(
    "/",
    response_model=list[schemas_bot.BotPublic],
)
async def read_bots(
        session: SessionDep,
        current_user: CurrentUser,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve bots.
    """
    if current_user.role == RoleType.ADMIN:
        bots = await BotModel.get_all(session, skip, limit, BotModel.default_eager_relationships)
        return bots
    else:
        statement = select(BotModel)
        options = BotModel.build_eager_loading_options(BotModel.default_eager_relationships, BotModel)
        statement = statement.options(*options)
        bots = await session.execute(
            statement.where(
                (BotModel.owner_id == current_user.id) |
                (BotModel.id.in_(
                    select(user_bot_access.c.bot_id).where(user_bot_access.c.user_id == current_user.id)
                ))
            ).offset(skip).limit(limit)
        )
        return bots.scalars().all()


@router.get("/{bot_id}",
            response_model=schemas_bot.BotPublic,
            dependencies=[CurrentBotViewer]
)
async def read_bot(
        bot_id: Union[UUID, str], session: SessionDep,
) -> Any:
    """
    Get a specific bot by id.
    """
    bot = await crud_bot.get_bot(session, bot_id)
    try:
        await cache_structure_bot(session, bot)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return bot


@router.post(
    "/",
    response_model=schemas_bot.BotPublic,
)
async def create_bot(session: SessionDep, bot_in: schemas_bot.BotCreate, current_user: CurrentDeveloperDep) -> Any:
    """
    Create a bot.
    """
    await crud_bot.check_bot_unique(session, bot_in)
    bot = await crud_bot.create_bot(session, bot_in, current_user)
    await session.commit()
    await session.refresh(bot)
    first_step = await crud_step.create_step(session, schemas_step.StepCreate(name="First step",
                                                                              bot_id=bot.id,
                                                                              is_proxy=False))
    await session.commit()
    await session.refresh(first_step)
    bot.first_step = first_step
    await session.commit()
    await session.refresh(bot, attribute_names=BotModel.list_select_related)
    return bot


@router.patch(
    "/{bot_id}",
    response_model=schemas_bot.BotPublic,
    dependencies=[CurrentBotEditor]
)
async def update_bot(
        bot_id: Union[UUID, str], session: SessionDep, bot_in: schemas_bot.BotUpdate
) -> Any:
    """
    Update a bot.
    """
    await crud_bot.check_bot_unique(session, bot_in, exclude_id=bot_id)
    bot = await crud_bot.update_bot(session, bot_id, bot_in)
    if bot_in.variables:
        variables = await crud_variables.full_update_variable_by_id(session, BotVariables, bot.id, bot_in.variables.data)
        await session.commit()
        await session.refresh(variables)

    await session.commit()
    await session.refresh(bot, attribute_names=["variables"])

    await update_cache_variables_bot(bot)
    return bot


@router.delete("/{bot_id}",
               dependencies=[CurrentBotEditor])
async def delete_bot(session: SessionDep, bot_id: Union[UUID, str]) -> Message:
    """
    Delete a bot.
    """
    bot = await crud_bot.get_bot(session, bot_id)
    bot.first_step = None
    await session.commit()
    await session.refresh(bot)
    await crud_bot.delete_bot(session, bot_id)
    await session.commit()
    return Message(message="Bot deleted successfully.")


@router.post("/{bot_id}/cache_structure",)
async def cache_structure(
        bot_id: Union[UUID, str], session: SessionDep,
) -> Message:
    """
    Cache bot structure.
    """
    bot = await crud_bot.get_bot(session, bot_id)
    try:
        await cache_structure_bot(session, bot)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return Message(message="Bot structure cached successfully.")


@router.get("/export/{bot_id}",
            # dependencies=[Depends(get_current_active_superuser)]

            )
async def export_bot(
        bot_id: Union[UUID, str], session: SessionDep, background_tasks: BackgroundTasks,
) -> Any:
    """
    Export a bot.
    """
    bot = await crud_bot.get_bot(session, bot_id)
    export_json = await export_bot_structure(session, bot)
    temp_file_path = await create_temp_json_file(export_json)
    background_tasks.add_task(os.remove, temp_file_path)
    return FileResponse(temp_file_path, media_type="application/json", filename=f"bot-{bot.id}.json")


@router.post(
    "/import",
    dependencies=[],
)
async def import_bot(
    session: SessionDep, 
    current_user: CurrentUser, 
    file: UploadFile = File(...),
    target_bot_id: UUID = Query(None, description="ID of existing bot to replace structure")
) -> Any:
    """
    Import a bot. If target_bot_id is provided, replaces existing bot structure.
    """
    try:
        contents = await file.read()
        data = json.loads(contents.decode())
        bot, is_replacement = await import_bot_structure(session, owner=current_user, data=data, target_bot_id=target_bot_id)

        bot_with_relations = await BotModel.get_obj(
            session, 
            bot.id, 
            eager_relationships=BotModel.default_eager_relationships
        )
        
        bot_public = schemas_bot.BotPublic.model_validate(bot_with_relations)
        
        if is_replacement:
            return JSONResponse(
                status_code=status.HTTP_200_OK, 
                content={
                    "message": "Bot structure replaced successfully.",
                    "bot": bot_public.model_dump(mode='json')
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED, 
                content={
                    "message": "Bot created successfully.",
                    "bot": bot_public.model_dump(mode='json')
                }
            )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/{bot_id}/grant_access",
             dependencies=[CurrentBotEditor])
async def grant_access(
        bot_id: Union[UUID, str], session: SessionDep, user_id: UUID, access_type: AccessType
) -> Message:
    """
    Grant a user access to a bot.
    """
    bot = await crud_bot.get_bot(session, bot_id)
    user = await crud_user.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await session.execute(
        insert(user_bot_access).values(user_id=user.id, bot_id=bot.id, access_type=access_type)
    )
    await session.commit()
    return Message(message="Access granted successfully.")


@router.post("/{bot_id}/revoke_access",
             dependencies=[CurrentBotEditor])
async def revoke_access(
        bot_id: Union[UUID, str], session: SessionDep, user_id: UUID
) -> Message:
    """
    Revoke a user's access to a bot.
    """
    bot = await crud_bot.get_bot(session, bot_id)
    user = await crud_user.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await session.execute(
        user_bot_access.delete().where(user_bot_access.c.user_id == user.id, user_bot_access.c.bot_id == bot.id)
    )
    await session.commit()
    return Message(message="Access revoked successfully.")
