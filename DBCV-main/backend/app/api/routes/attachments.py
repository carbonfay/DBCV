from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from pathlib import Path
from app.config import settings
import app.crud.attachment as crud_attachment
import app.schemas.attachment as schemas_attachment
from app.api.dependencies.db import SessionDep
from app.models.attachment import AttachmentModel
from app.schemas.message import Message
from app.api.dependencies.auth import get_current_user, CurrentUser, CurrentDeveloper, CurrentAdmin

router = APIRouter()


@router.get(
    "/",
    dependencies=[CurrentAdmin],
    response_model=list[schemas_attachment.AttachmentPublic],
)
async def read_attachments(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(gt=0)] = None,
) -> Any:
    """
    Retrieve attachments.
    """
    statement = select(AttachmentModel).offset(skip)
    if limit:
        statement = statement.limit(limit)
    attachments = list((await session.scalars(statement)).all())
    return attachments


@router.get(
    "/download",
    response_class=StreamingResponse,
    responses={
        200: {"description": "File stream"},
        404: {"description": "Attachment content not found"}
    }
)
async def download_attachment_file(session: SessionDep, attachment_id: UUID | str):
    """
    Create a attachment file.
    """
    attachment = await crud_attachment.get_attachment(session, attachment_id)
    from app.services.s3_service import object_exists, upload_bytes, stream_object

    key = str(attachment.file)
    exists = await object_exists(key)
    if not exists:
        legacy_path = Path(settings.MEDIA_ROOT / "attachment" / (attachment.file_name or ""))
        if legacy_path.exists() and legacy_path.is_file():
            data = legacy_path.read_bytes()
            await upload_bytes(key, data, content_type=attachment.content_type)
        else:
            # If no legacy file and no S3 object, return 404
            raise HTTPException(status_code=404, detail="Attachment content not found")

    # Stream file from S3
    iterator, headers = await stream_object(key)
    filename = attachment.file_name or "file"
    headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
    return StreamingResponse(iterator, media_type=headers.get("Content-Type", "application/octet-stream"), headers=headers)


@router.post(
    "/",
    dependencies=[CurrentDeveloper],
    response_model=schemas_attachment.AttachmentPublic,
)
async def create_attachment(session: SessionDep, file: UploadFile = File(...)) -> Any:
    """
    Create a attachment.
    """
    attachment = await crud_attachment.create_attachment(session, file)
    await session.commit()
    await session.refresh(attachment)

    return attachment



