from typing import Annotated, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

import app.crud.user as crud_user
import app.schemas.user as schemas_user
from app.api.dependencies.auth import CurrentUser, CurrentAdmin
from app.api.dependencies.db import SessionDep
from app.models.role import RoleType
from app.models.user import UserModel
from app.schemas.message import Message
from app.utils.auth import get_password_hash, verify_password

router = APIRouter()


@router.get("/me", response_model=schemas_user.UserPublic)
async def read_user_me(*, session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Retrieve own user.
    """
    return await crud_user.get_user(session, current_user.id, UserModel.full_eager_relationships)


@router.patch("/me", response_model=schemas_user.UserPublic)
async def update_user_me(*,
                         session: SessionDep, user_in: schemas_user.UserUpdateMe, current_user: CurrentUser
                         ) -> Any:
    """
    Update own user.
    """
    await crud_user.check_user_unique(session, user_in, exclude_id=current_user.id)
    user = await crud_user.update_user(session, current_user.id, user_in)
    await session.commit()
    await session.refresh(user)
    return user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
        *, session: SessionDep, body: schemas_user.UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password.")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the current one.",
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    await session.commit()
    return Message(message="Password updated successfully.")


@router.get(
    "/",
    dependencies=[CurrentAdmin],
    response_model=list[schemas_user.UserPublic],
)
async def read_users(
        session: SessionDep,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve users.
    """
    return await UserModel.get_all(session, skip, limit)


@router.get("/{user_id}", response_model=schemas_user.UserPublic)
async def read_user(
        user_id: Union[UUID, str], session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    if current_user.id != user_id and not current_user.role == RoleType.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges.",
        )
    return await crud_user.get_user(session, user_id)


@router.post(
    "/",
    dependencies=[CurrentAdmin],
    response_model=schemas_user.UserPublic,
)
async def create_user(session: SessionDep, user_in: schemas_user.UserCreate) -> Any:
    """
    Create a user.
    """
    await crud_user.check_user_unique(session, user_in)
    user = await crud_user.create_user(session, user_in)
    await session.commit()
    await session.refresh(user)
    return user


@router.patch(
    "/{user_id}",
    dependencies=[CurrentAdmin],
    response_model=schemas_user.UserPublic,
)
async def update_user(
        user_id: Union[UUID, str], session: SessionDep, user_in: schemas_user.UserUpdate
) -> Any:
    """
    Update a user.
    """
    await crud_user.check_user_unique(session, user_in, exclude_id=user_id)
    user = await crud_user.update_user(session, user_id, user_in)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}", dependencies=[CurrentAdmin])
async def delete_user(session: SessionDep, user_id: Union[UUID, str]) -> Message:
    """
    Delete a user.
    """
    await crud_user.delete_user(session, user_id)
    await session.commit()
    return Message(message="User deleted successfully.")
