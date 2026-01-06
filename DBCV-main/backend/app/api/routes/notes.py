from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

import app.crud.note as crud_note
import app.schemas.note as schemas_note
from app.api.dependencies.db import SessionDep
from app.models.note import NoteModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentAdmin

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentAdmin],
    response_model=list[schemas_note.NotePublic],
)
async def read_notes(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve notes.
    """
    statement = select(NoteModel).offset(skip)
    if limit:
        statement = statement.limit(limit)
    return list((await session.scalars(statement)).all())


@router.post(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=schemas_note.NotePublic,
)
async def create_note(session: SessionDep, note_in: schemas_note.NoteCreate) -> Any:
    """
    Create a note.
    """
    note = await crud_note.create_note(session, note_in)
    await session.commit()
    await session.refresh(note)
    return note


@router.patch(
    "/{note_id}",
    dependencies=[CurrentDeveloper],
    response_model=schemas_note.NotePublic,
)
async def update_note(
    note_id: Union[UUID, str], session: SessionDep, note_in: schemas_note.NoteUpdate
) -> Any:
    """
    Update a note.
    """
    note = await crud_note.update_note(session, note_id, note_in)
    await session.commit()
    await session.refresh(note)
    return note


@router.delete("/{note_id}",
               dependencies=[CurrentDeveloper],
               response_model=Message)
async def delete_note(session: SessionDep, note_id: Union[UUID, str]) -> Message:
    """
    Delete a note.
    """
    await crud_note.delete_note(session, note_id)
    await session.commit()
    return Message(message="Note deleted successfully.")