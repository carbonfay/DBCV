from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.models.note import NoteModel
from app.schemas import note as schemas_note


async def get_note(session: AsyncSession, note_id: UUID | str,
                   eager_relationships: Optional[Dict[str, Any]] = None,) -> Type[NoteModel]:
    note = await NoteModel.get_obj(session, note_id, eager_relationships)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    return note


async def create_note(
    session: AsyncSession, note_in: schemas_note.NoteCreate,
) -> NoteModel:
    db_obj = NoteModel(
        **note_in.model_dump(),
    )
    session.add(db_obj)
    return db_obj


async def update_note(
    session: AsyncSession,
    note_id: UUID | str,
    note_in: schemas_note.NoteUpdate,
) -> Type[NoteModel]:
    note = await get_note(session, note_id)
    for key, value in note_in.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    return note


async def delete_note(session: AsyncSession, note_id: UUID | str) -> None:
    await session.delete(await get_note(session, note_id))


