from __future__ import annotations

from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies.db import SessionDep
from app.api.dependencies.auth import CurrentBotEditor, CurrentBotViewer
from app.schemas import credentials as schemas_cred
from app.crud import credentials as crud_cred

router = APIRouter(tags=["credentials"])


@router.get(
    "/",
    response_model=list[schemas_cred.CredentialListItem],
    dependencies=[CurrentBotViewer],
)
async def read_credentials(
    bot_id: Union[UUID, str],
    session: SessionDep
) -> Any:
    """
    Retrieve credentials for a bot (public meta, no payload).
    """
    items = await crud_cred.list_bot_credentials(session, bot_id)
    return items


@router.get(
    "/{cred_id}",
    response_model=schemas_cred.CredentialPublic,
    dependencies=[CurrentBotViewer],
)
async def read_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
) -> Any:
    """
    Get a specific credential by id (public meta, no payload).
    """
    cred = await crud_cred.get_credential(session, cred_id, bot_id=bot_id)
    return cred


@router.post(
    "/",
    response_model=schemas_cred.CredentialCreateOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[CurrentBotEditor],
)
async def create_credential(
    bot_id: Union[UUID, str],
    session: SessionDep,
    cred_in: schemas_cred.CredentialCreate,
) -> Any:
    """
    Create a credential for a bot (payload is encrypted before store).
    """
    if str(cred_in.bot_id) != str(bot_id):
        raise HTTPException(status_code=422, detail="bot_id mismatch with path")

    try:
        cred = await crud_cred.create_credential(session, cred_in)
        await session.commit()
        await session.refresh(cred)
        return cred
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Integrity error: default constraint failed") from e


@router.patch(
    "/{cred_id}",
    response_model=schemas_cred.CredentialUpdateOut,
    dependencies=[CurrentBotEditor],
)
async def update_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
    cred_in: schemas_cred.CredentialUpdate,
) -> Any:
    """
    Update a credential (meta and/or payload). Enforces single default.
    """
    try:
        cred = await crud_cred.update_credential(session, cred_id, bot_id, cred_in)
        await session.commit()
        await session.refresh(cred)
        return cred
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Integrity error: default constraint failed") from e


@router.post(
    "/{cred_id}/make-default",
    response_model=schemas_cred.CredentialPublic,
    dependencies=[CurrentBotEditor],
)
async def make_default_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
) -> Any:
    """
    Mark credential as default within (bot, provider, strategy).
    """
    cred = await crud_cred.get_credential(session, cred_id, bot_id=bot_id)
    cred.is_default = True
    await crud_cred._unset_other_defaults(
        session, bot_id=cred.bot_id, provider=cred.provider, strategy=cred.strategy, except_id=cred.id
    )
    await session.commit()
    await session.refresh(cred)
    return cred


@router.delete(
    "/{cred_id}",
    dependencies=[CurrentBotEditor],
)
async def delete_credential(
    bot_id: Union[UUID, str],
    cred_id: Union[UUID, str],
    session: SessionDep,
) -> Any:
    """
    Delete a credential.
    """
    await crud_cred.delete_credential(session, cred_id, bot_id)
    await session.commit()
    return {"message": "Credential deleted successfully."}
