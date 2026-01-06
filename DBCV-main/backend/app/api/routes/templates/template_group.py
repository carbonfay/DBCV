from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

import app.schemas.template_group as schemas_group
from app.models.role import RoleType
from app.models.template_group import TemplateGroupModel
from app.models.template import TemplateModel
from app.api.dependencies.db import SessionDep
from app.api.dependencies.auth import CurrentDeveloper, CurrentDeveloperDep, CurrentAdmin, CurrentAdminDep
import app.crud.template_group as crud_group
from app.schemas.message import Message

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=list[schemas_group.TemplateGroupPublic],
)
async def read_template_groups(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve all template groups.
    """
    return await TemplateGroupModel.get_all(session, skip, limit)


@router.get(
    "/{group_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_group.TemplateGroupPublic,
)
async def read_template_group(
    session: SessionDep,
    group_id: Union[UUID, str],
) -> Any:
    """
    Retrieve one template group by ID.
    """
    return await crud_group.get_template_group(session, group_id)


@router.post(
    "/",
    dependencies=[CurrentAdmin],
    response_model=schemas_group.TemplateGroupPublic,
)
async def create_template_group(
    session: SessionDep,
    group_in: schemas_group.TemplateGroupCreate,
    owner: CurrentAdminDep,
) -> Any:
    """
    Create a new template group.
    """
    group = await crud_group.create_template_group(session, group_in)
    group.owner_id = owner.id
    await session.commit()
    await session.refresh(group)
    return group


@router.patch(
    "/{group_id}",
    dependencies=[CurrentAdmin],
    response_model=schemas_group.TemplateGroupPublic,
)
async def update_template_group(
    session: SessionDep,
    group_id: Union[UUID, str],
    group_in: schemas_group.TemplateGroupUpdate,
    current_user: CurrentAdminDep,
) -> Any:
    """
    Update a template group.
    """
    group = await crud_group.update_template_group(session, group_id, group_in)
    await session.commit()
    await session.refresh(group)
    return group


@router.delete(
    "/{group_id}",
    dependencies=[CurrentAdmin],
    response_model=Message,
)
async def delete_template_group(
    session: SessionDep,
    group_id: Union[UUID, str],
) -> Message:
    """
    Delete a template group.
    """
    group = await crud_group.get_template_group(session, group_id)
    await crud_group.delete_template_group(session, group_id)
    await session.commit()
    return Message(message="Template group deleted successfully.")


@router.post(
    "/{group_id}/add_template/{template_id}",
    dependencies=[CurrentAdmin],
    response_model=Message,
)
async def add_template_to_group(
    session: SessionDep,
    group_id: UUID,
    template_id: UUID,
) -> Message:
    """
    Add a template to a group.
    """
    group = await crud_group.get_template_group(session, group_id)
    template = await session.get(TemplateModel, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.group_id = group_id
    await session.commit()
    return Message(message=f"Template {template_id} added to group {group_id}.")


@router.post(
    "/{group_id}/bulk_add",
    dependencies=[CurrentAdmin],
    response_model=Message,
)
async def bulk_add_templates_to_group(
    session: SessionDep,
    group_id: UUID,
    body: schemas_group.TemplateGroupBulkAdd,
) -> Message:
    """
    Add multiple templates to a group.
    """
    group = await crud_group.get_template_group(session, group_id)
    if not body.template_ids:
        return Message(message="No templates provided.")

    result_added = 0
    for template_id in body.template_ids:
        template = await session.get(TemplateModel, template_id)
        if template:
            template.group_id = group_id
            result_added += 1

    await session.commit()
    return Message(message=f"Added {result_added} templates to group {group_id}.")


@router.post(
    "/{group_id}/remove_template/{template_id}",
    dependencies=[CurrentAdmin],
    response_model=Message,
)
async def remove_template_from_group(
    session: SessionDep,
    group_id: UUID,
    template_id: UUID,
) -> Message:
    """
    Remove a template from a group (detach without deleting template).
    """
    group = await crud_group.get_template_group(session, group_id)
    template = await session.get(TemplateModel, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.group_id != group_id:
        raise HTTPException(status_code=400, detail="Template does not belong to this group")
    template.group_id = None
    await session.commit()
    return Message(message=f"Template {template_id} removed from group {group_id}.")
