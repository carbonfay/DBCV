from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict
from app.api.dependencies.auth import get_current_user, CurrentUser
from app.models.user import UserModel
import asyncio
import logging
from app.config import settings
from app.crud.bot import get_bot
from app.api.dependencies.db import SessionDep

templates = Jinja2Templates(directory=settings.TEMPLATES_ROOT)

router = APIRouter()


# Страница конструктора бота
@router.get("/{bot_id}", response_class=HTMLResponse, summary="Bot Constructor Page")
async def get_bot_constructor_page(session: SessionDep, bot_id: UUID | str, request: Request, current_user: CurrentUser):
    bot = await get_bot(session, bot_id)
    return templates.TemplateResponse("constructor.html",
                                      {"request": request, "user": current_user, 'bot': bot})


@router.get("/", response_class=HTMLResponse, summary="Bot Constructor Page")
async def get_bot_constructor_page(session: SessionDep, request: Request):
    return templates.TemplateResponse("constructor.html",
                                      {"request": request,})