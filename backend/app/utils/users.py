import string
import random
from uuid import uuid4

from app.models.user import UserModel
from app.models.anonymous_user import AnonymousUserModel
from app.api.dependencies.db import SessionDep
from fastapi import HTTPException


async def get_any_user(session, user_id) -> UserModel | AnonymousUserModel:
    user = await session.get(UserModel, user_id)
    if user is None:
        user = await session.get(AnonymousUserModel, user_id)
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user.")
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def normalize_user_data(user_fields: dict) -> dict:
    username = user_fields.get("username") or f"user_{uuid4().hex[:8]}"
    email = user_fields.get("email") or f"{username}@noemail.local"

    return {
        "username": username,
        "email": email,
        "password": "".join(random.choices(string.ascii_letters + string.digits, k=10))
    }


