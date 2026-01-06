from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

import app.crud.template as crud_template
import app.crud.step as crud_step
import app.schemas.templates as schemas_template
import app.schemas.step as schemas_step
from app.api.dependencies.db import SessionDep
from app.models import StepModel
from app.models.role import RoleType
from app.models.template import TemplateModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentDeveloperDep, CurrentAdmin, CurrentAdminDep

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_template.TemplatePublic],
)
async def read_templates(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve templates.
    """
    return await TemplateModel.get_all(session, skip, limit)


@router.get(
    "/{template_id}",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_template.TemplatePublic],
)
async def read_template(
    session: SessionDep,
    template_id: Union[UUID, str],
) -> Any:
    """
    Retrieve template.
    """
    return await TemplateModel.get_obj(session, template_id)


@router.post(
    "/",
    dependencies=[CurrentAdmin],
    response_model=schemas_template.TemplatePublic,
)
async def create_template(session: SessionDep, template_in: schemas_template.TemplateCreateData, owner: CurrentAdminDep) -> Any:
    """
    Create a template.
    """

    steps = [await crud_step.get_step(session, step_id, StepModel.default_eager_relationships) for step_id in template_in.step_ids]

    if any(step is None for step in steps):
        raise ValueError("Один или несколько шагов не найдены в базе данных.")

    steps_json = [schemas_step.StepTemplate(**step.__dict__).dict() for step in steps]
    template_json = schemas_template.TemplateCreate(**template_in.model_dump(exclude={"step_ids"}),
                                                    steps=steps_json,
                                                    owner_id=owner.id)
    template = await crud_template.create_template(session, template_json)

    await session.commit()
    await session.refresh(template)

    return template


@router.patch(
    "/{template_id}",
    dependencies=[CurrentAdmin],
    response_model=schemas_template.TemplatePublic,
)
async def update_template(
        template_id: Union[UUID, str],
        session: SessionDep, template_in: schemas_template.TemplateUpdateData,
) -> Any:
    """
    Update a template.
    """
    template = await crud_template.get_template(session, template_id)
    steps = [await crud_step.get_step(session, step_id, StepModel.default_eager_relationships) for step_id in template_in.step_ids]

    if any(step is None for step in steps):
        raise ValueError("Один или несколько шагов не найдены в базе данных.")

    steps_json = [schemas_step.StepTemplate(**step.__dict__).dict() for step in steps]
    template_json = schemas_template.TemplateUpdate(**template_in.model_dump(exclude={"step_ids"}),
                                                    steps=steps_json,)
    template = await crud_template.update_template(session, template_id, template_json)
    await session.commit()
    await session.refresh(template)
    return template


@router.delete("/{template_id}",
               dependencies=[CurrentAdmin],
               response_model=Message
)
async def delete_template(session: SessionDep,
                          template_id: Union[UUID, str],
) -> Message:
    """
    Delete a template.
    """
    template = await crud_template.get_template(session, template_id)
    await crud_template.delete_template(session, template_id)
    await session.commit()
    return Message(message="Template deleted successfully.")