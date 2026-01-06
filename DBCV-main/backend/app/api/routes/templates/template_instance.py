from typing import Annotated, Any, Union
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.models.access import AccessType
from app.models.step import StepModel
from app.models.connection import ConnectionGroupModel, ConnectionModel

import app.crud.template_instance as crud_template_instance
import app.crud.template as crud_template
import app.crud.bot as crud_bot
import app.crud.step as crud_step
import app.schemas.templates as schemas_template
import app.schemas.step as schemas_step
from app.api.dependencies.db import SessionDep
from app.models.template import TemplateModel
from app.models.template_instance import TemplateInstanceModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, BotAccessChecker

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_template.TemplateInstancePublic],
)
async def read_templates(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve templates.
    """
    return await TemplateInstanceModel.get_all(session, skip, limit)


@router.get(
    "/{template_id}",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_template.TemplateInstancePublic],
)
async def read_template(
    session: SessionDep,
    template_id: Union[UUID, str],
) -> Any:
    """
    Retrieve template.
    """
    return await TemplateInstanceModel.get_obj(session, template_id)


@router.post(
    "/",
    response_model=schemas_step.StepPublic,
)
async def create_template_instance_and_insert(
    session: SessionDep,
    bot_id: str | UUID,
    template_in: schemas_template.TemplateInstanceCreateAndInsert,
    current_user: CurrentUser,
) -> Any:
    """
    Создаёт TemplateInstance, шаг и связанные группы связи/связи.
    """
    await BotAccessChecker._has_access(session, bot_id, current_user, AccessType.EDITOR)

    template: TemplateModel = await crud_template.get_template(session, template_in.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    instance_in = schemas_template.TemplateInstanceCreate(
        name=f"Template instance: {template.name}",
        template_id=str(template.id),
        inputs_mapping=template_in.inputs_mapping,
        outputs_mapping=template_in.outputs_mapping,
        variables=template_in.variables,
        steps=template.steps,
        first_step_id=template.first_step_id
    )
    instance = await crud_template_instance.create_template(session, instance_in)
    await session.commit()
    await session.refresh(instance)

    step = StepModel(
        name=f"Template: {template.name}",
        is_proxy=True,
        template_instance_id=instance.id,
        bot_id=bot_id,
        pos_x=template_in.pos_x,
        pos_y=template_in.pos_y
    )
    session.add(step)

    await session.commit()
    await session.refresh(step, ["template_instance", "connection_groups", "message"])
    from pydantic import ValidationError
    try:
        step_schemas = schemas_step.StepPublic.from_orm(step)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    return step_schemas


@router.patch(
    "/{template_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_template.TemplateInstancePublic,
)
async def update_template(
    template_id: Union[UUID, str], session: SessionDep, template_in: schemas_template.TemplateInstanceUpdate
) -> Any:
    """
    Update a template_instance.
    """
    template_instance = await crud_template_instance.update_template(session, template_id, template_in)
    await session.commit()
    await session.refresh(template_instance)
    return template_instance


@router.delete("/{template_id}",
               dependencies=[CurrentDeveloper],
               response_model=Message)
async def delete_template(session: SessionDep, template_id: Union[UUID, str]) -> Message:
    """
    Delete a template_instance.
    """
    await crud_template_instance.delete_template(session, template_id)
    await session.commit()
    return Message(message="TemplateInstance deleted successfully.")