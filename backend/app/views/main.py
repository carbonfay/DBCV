from fastapi import FastAPI, Request, APIRouter

from app.views.routes import auth, chat, bot
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from app.exceptions import TokenExpiredException, TokenNoFoundException


views_router = FastAPI()

views_router.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников. Можете ограничить список доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки

)

views_router.include_router(auth.router, prefix="/auth", tags=["auth"])
views_router.include_router(chat.router, prefix="/chat", tags=["chat"])
views_router.include_router(bot.router, prefix="/bot", tags=["bot"])


@views_router.get("/")
async def redirect_to_auth():
    return RedirectResponse(url="/auth")


@views_router.exception_handler(TokenExpiredException)
async def token_expired_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/auth")


@views_router.exception_handler(TokenNoFoundException)
async def token_no_found_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/auth")