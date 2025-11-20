from typing import Type, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserModel
from app.models.template import TemplateModel
from app.schemas import templates as schemas_templates
from app.crud.utils import is_object_unique
from fastapi import HTTPException


async def get_template(session: AsyncSession, template_id: UUID | str,
                  eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[TemplateModel]:
    template = await TemplateModel.get_obj(session, template_id, eager_relationships)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    return template


async def create_template(
        session: AsyncSession, template_in: schemas_templates.TemplateCreate,
) -> TemplateModel:
    db_obj = TemplateModel(
        **template_in.model_dump(exclude={"steps_id"}),

    )
    session.add(db_obj)
    return db_obj


async def update_template(
        session: AsyncSession,
        template_id: UUID | str,
        template_in: schemas_templates.TemplateUpdate,
) -> Type[TemplateModel]:
    template = await get_template(session, template_id)
    for key, value in template_in.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    return template


async def delete_template(session: AsyncSession, template_id: UUID | str) -> None:
    await session.delete(await get_template(session, template_id))
