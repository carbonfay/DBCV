import json
from typing import Annotated, Any, List, Dict, Union, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, \
    BackgroundTasks, Form
from sqlalchemy import select
import logging
import app.crud.message as crud_message
import app.schemas.message as schemas_message
from app.api.dependencies.db import SessionDep
from app.api.routes.sockets import notify_channel
from app.broker import broker
from app.models.access import AccessType
from app.models.message import MessageModel
from app.models.role import RoleType
from app.schemas.message import Message
from app.api.dependencies.auth import CurrentUser, CurrentAnyUser, CurrentDeveloper, CurrentAdmin, BotAccessChecker
from app.exceptions import ForbiddenException
from app.api.routes.emitters import update_emitter
from app.schemas.emitter import EmitterUpdate
from fastapi.responses import JSONResponse
import app.utils.message as message_utils
from app.utils.message import publish_message

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentAdmin],
    response_model=list[schemas_message.MessagePublic],
)
async def read_messages(
        session: SessionDep,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve messages.
    """
    statement = select(MessageModel).offset(skip)
    if limit:
        statement = statement.limit(limit)
    return list((await session.scalars(statement)).all())


async def validate_message_access(step_id: Optional[Union[str, UUID]], emitter_id: Optional[Union[str, UUID]], current_user: CurrentUser, session: SessionDep):
    """
    Validate access to step or emitter for the current user.
    """
    if step_id:
        await BotAccessChecker._has_access_by_step(session, step_id, current_user, AccessType.EDITOR)
    if emitter_id:
        await BotAccessChecker._has_access_by_emitter(session, emitter_id, current_user, AccessType.EDITOR)


@router.post(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=schemas_message.MessagePublic,
)
async def create_message(session: SessionDep,
                         current_user: CurrentUser,
                         text: str = Form(""),
                         params: Optional[str] = Form(None),
                         recipient_id: Optional[Union[UUID, str]] = Form(None),
                         sender_id: Optional[Union[UUID, str]] = Form(None),
                         widget_id: Optional[Union[str, UUID]] = Form(None),
                         step_id: Optional[Union[str, UUID]] = Form(None),
                         emitter_id: Optional[Union[str, UUID]] = Form(None),
                         channel_id: Optional[Union[str, UUID]] = Form(None),
                         attachments: List[UploadFile] = []):
    """
    Create a message step or emitter.
    """
    await validate_message_access(step_id, emitter_id, current_user, session)

    try:
        message_data = {
            "text": text,
            "params": json.loads(params) if params else None,
            "recipient_id": recipient_id,
            "sender_id": sender_id,
            "widget_id": widget_id,
            "step_id": step_id,
            "channel_id": channel_id,
        }
        if recipient_id is not None and recipient_id != current_user.id:
            return ForbiddenException
        message_in = schemas_message.MessagePrivateCreate(**message_data)
        message = await message_utils.create_message(session, current_user, message_in, attachments)
        if emitter_id:
            await update_emitter(emitter_id, session, EmitterUpdate(message_id=message.id), current_user)
        return message

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post(
    "/send_message",
    response_model=schemas_message.MessagePublic,
)
async def send_message(session: SessionDep,
                       current_user: CurrentAnyUser,
                       text: str = Form(""),
                       recipient_id: Optional[Union[UUID, str]] = Form(None),
                       channel_id: Optional[Union[str, UUID]] = Form(None),
                       attachments: List[UploadFile] = []):
    """
    Create a message.
    """
    message_data = {
        "text": text,
        "recipient_id": recipient_id,
        "sender_id": current_user.id,
        "channel_id": channel_id,
    }
    message_in = schemas_message.MessageCreate(**message_data)
    message = await message_utils.create_message(session, current_user, message_in, attachments)
    await notify_channel(message.channel_id, schemas_message.MessagePublic(**message.__dict__))
    await publish_message(message)
    return message


@router.get("/{message_id}",
            dependencies=[CurrentDeveloper],
            response_model=schemas_message.MessagePublic)
async def read_message(
        message_id: Union[UUID, str], session: SessionDep,
) -> Any:
    """
    Get a specific message by id.
    """
    return await crud_message.get_message(session, message_id, MessageModel.default_eager_relationships)


async def check_message_permissions(session: SessionDep, message_id: UUID, current_user: CurrentAnyUser) -> None:
    message = await crud_message.get_message(session, message_id, eager_relationships={})
    if message.step_id:
        return await BotAccessChecker._has_access_by_step(session, message.step_id, current_user, AccessType.EDITOR)
    if message.sender_id and message.sender_id != current_user.id or hasattr(current_user, "role") and current_user.role != RoleType.ADMIN:
        raise ForbiddenException


@router.patch(
    "/{message_id}",
    response_model=schemas_message.MessagePublic,
)
async def update_message(
        message_id: Union[UUID, str], session: SessionDep, message_in: schemas_message.MessagePrivateUpdate, current_user: CurrentAnyUser,
) -> Any:
    """
    Update a message.
    """
    await check_message_permissions(session, message_id, current_user)
    message = await crud_message.update_message(session, message_id, message_in)
    await session.commit()
    await session.refresh(message, attribute_names=["sender", "recipient", "widget", "attachments"])
    return message


@router.delete("/{message_id}",
               response_model=Message)
async def delete_message(session: SessionDep, message_id: Union[UUID, str], current_user: CurrentAnyUser) -> Message:
    """
    Delete a message.
    """
    await check_message_permissions(session, message_id, current_user)
    await crud_message.delete_message(session, message_id)
    await session.commit()
    return Message(message="Message deleted successfully.")
