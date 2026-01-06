from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict
from app.schemas.message import MessagePublic, MessageCreate
from app.schemas.user import UserPublic
from app.api.dependencies.auth import get_current_user, CurrentUser
from app.models.user import UserModel
import asyncio
import logging
from app.config import settings
from app.api.routes.channels import read_user_channels
from app.api.dependencies.db import SessionDep

templates = Jinja2Templates(directory=settings.TEMPLATES_ROOT)

router = APIRouter()


# Страница чата
@router.get("/", response_class=HTMLResponse, summary="Chat Page")
async def get_chat_page(session: SessionDep, request: Request, current_user: CurrentUser):
    channels = await read_user_channels(session, current_user)
    return templates.TemplateResponse("chat.html",
                                      {"request": request, "user": current_user, 'channels': channels})
