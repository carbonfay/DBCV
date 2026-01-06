from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

import app.schemas.user as schemas_user
from app.crud.utils import is_object_unique
from app.models.user import UserModel
from app.utils.auth import get_password_hash, verify_password


async def check_user_unique(
        session: AsyncSession,
        user_in: schemas_user.UserBase | schemas_user.UserUpdateMe,
        exclude_id: UUID | str | None = None,
) -> None:
    if not await is_user_unique(session, user_in, exclude_id):
        raise HTTPException(
            status_code=400,
            detail="The user with the given email or username already exists.",
        )


async def is_user_unique(
        session: AsyncSession,
        user_in: schemas_user.UserBase | schemas_user.UserUpdateMe,
        exclude_id: UUID | str | None = None,
) -> bool:
    return await is_object_unique(
        session,
        UserModel,
        user_in,
        unique_fields=("email", "username"),
        exclude_id=exclude_id,
    )


async def authenticate(
        session: AsyncSession, username: str, password: str
) -> UserModel | None:
    db_user = await get_user_by_username(session, username)
    if not (db_user and verify_password(password, db_user.hashed_password)):
        return None
    return db_user


async def get_user(session: AsyncSession, user_id: UUID | str,
                   eager_relationships: Optional[Dict[str, Any]] = None, ) -> Type[UserModel]:
    user = await UserModel.get_obj(session, user_id, eager_relationships)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


async def get_user_by_unique_field(
        session: AsyncSession, field: str, value: str
) -> UserModel | None:
    return (
        await session.scalars(select(UserModel).where(getattr(UserModel, field) == value))
    ).one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> UserModel | None:
    return await get_user_by_unique_field(session, "email", email)


async def get_user_by_username(session: AsyncSession, username: str) -> UserModel | None:
    return await get_user_by_unique_field(session, "username", username)


async def get_user_by_username_or_email(
    session: AsyncSession,
    username: str | None = None,
    email: str | None = None
) -> UserModel | None:
    if not username and not email:
        return None

    stmt = select(UserModel).where(
        or_(
            UserModel.username == username if username else False,
            UserModel.email == email if email else False,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_user(session: AsyncSession, user_in: schemas_user.UserCreate) -> UserModel | None:
    user = await get_user_by_username_or_email(session, username=user_in.username, email=user_in.email)
    if user:
        return user

    is_unique = await is_user_unique(session, user_in)
    if not is_unique:
        return None

    new_user = await create_user(session, user_in)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def create_user(
        session: AsyncSession, user_in: schemas_user.UserCreate
) -> UserModel:
    db_obj = UserModel(
        **user_in.model_dump(exclude={"password"}),
        hashed_password=get_password_hash(user_in.password)
    )
    session.add(db_obj)
    return db_obj


async def delete_user(session: AsyncSession, user_id: UUID | str) -> None:
    await session.delete(await get_user(session, user_id))


async def update_user(
        session: AsyncSession,
        user_id: UUID | str,
        user_in: schemas_user.UserUpdate | schemas_user.UserUpdateMe,
) -> UserModel:
    user = await get_user(session, user_id)
    for key, value in user_in.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    return user
