from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from starlette.responses import HTMLResponse

from app.utils.auth import create_access_token
from app.config import settings

from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException, PasswordMismatchException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.db import SessionDep
from app.api.routes.login import login_access_token
from fastapi.templating import Jinja2Templates
from app.database import get_db_session
templates = Jinja2Templates(directory=settings.TEMPLATES_ROOT)


router = APIRouter()


@router.get("/", response_class=HTMLResponse, summary="Страница авторизации")
async def auth(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


# @router.post("/register/")
# async def register_user(user_data: SUserRegister) -> dict:
#     user = await UsersDAO.find_one_or_none(email=user_data.email)
#     if user:
#         raise UserAlreadyExistsException
#
#     if user_data.password != user_data.password_check:
#         raise PasswordMismatchException("Пароли не совпадают")
#     hashed_password = get_password_hash(user_data.password)
#     await UsersDAO.add(
#         name=user_data.name,
#         email=user_data.email,
#         hashed_password=hashed_password
#     )
#
#     return {'message': 'Вы успешно зарегистрированы!'}
#
#
@router.post("/login/")
async def login(session: SessionDep, response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    access_token = await login_access_token(session, form_data)
    response.set_cookie(key="user_access_token", value=access_token.access_token, httponly=True)
    return {'ok': True, 'access_token': access_token, 'refresh_token': None, 'message': 'Авторизация успешна!'}


# @router.post("/logout/")
# async def logout_user(response: Response):
#     response.delete_cookie(key="user_access_token")
#     return {'message': 'Пользователь успешно вышел из системы'}