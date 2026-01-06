from typing import Type, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.template_group import TemplateGroupModel
from app.schemas import template_group as schemas_template_group
from fastapi import HTTPException


async def get_template_group(session: AsyncSession, template_group_id: UUID | str,
                  eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[TemplateGroupModel]:
    template_group = await TemplateGroupModel.get_obj(session, template_group_id, eager_relationships)
    if not template_group:
        raise HTTPException(status_code=404, detail="TemplateGroup not found.")
    return template_group


async def create_template_group(
        session: AsyncSession, template_group_in: schemas_template_group.TemplateGroupCreate,
) -> TemplateGroupModel:
    db_obj = TemplateGroupModel(
        **template_group_in.model_dump(),

    )
    session.add(db_obj)
    return db_obj


async def update_template_group(
        session: AsyncSession,
        template_group_id: UUID | str,
        template_group_in: schemas_template_group.TemplateGroupUpdate,
) -> Type[TemplateGroupModel]:
    template_group = await get_template_group(session, template_group_id)
    for key, value in template_group_in.model_dump(exclude_unset=True).items():
        setattr(template_group, key, value)
    return template_group


async def delete_template_group(session: AsyncSession, template_group_id: UUID | str) -> None:
    await session.delete(await get_template_group(session, template_group_id))
