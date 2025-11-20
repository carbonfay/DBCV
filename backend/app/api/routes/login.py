from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.db import SessionDep
from app.config import settings
from app.crud.user import authenticate
from app.schemas.auth import Token
from app.utils.auth import create_access_token

router = APIRouter()
from app.exceptions import IncorrectUsernameOrPasswordException, UserInactiveException
from app.crud.anonymous_user import create_anonymous_user


@router.post("/login/access-token")
async def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await authenticate(
        session=session, username=form_data.username, password=form_data.password
    )
    if not user:
        raise IncorrectUsernameOrPasswordException
    elif not user.is_active:
        raise UserInactiveException
    access_token_expiration = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(
            user.id, expiration_delta=access_token_expiration
        )
    )


@router.post("/login/anonymous-access-token")
async def anonymous_access_token(
    session: SessionDep
) -> Token:
    """
    Get access token for anonymous user.
    """
    user = await create_anonymous_user(session)
    await session.commit()
    await session.refresh(user)
    access_token_expiration = timedelta(minutes=settings.ANONYMOUS_ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(
            user.id, expiration_delta=access_token_expiration
        )
    )
