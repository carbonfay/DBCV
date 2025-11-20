from typing import Type, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import AttachmentModel
from app.services.attachment_service import AttachmentService
from app.services.s3_service import upload_bytes


async def get_attachment(session: AsyncSession, attachment_id: UUID | str,
                         eager_relationships: Optional[Dict[str, Any]] = None) -> Type[AttachmentModel]:
    attachment = await AttachmentModel.get_obj(session, attachment_id, eager_relationships)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    return attachment


async def create_attachment(
        session: AsyncSession,
        file: UploadFile,
) -> AttachmentModel:

    filename = file.filename or "file"
    data = await file.read()
    key, _ = AttachmentService.build_storage_key(filename, file.content_type)
    await upload_bytes(key, data, content_type=file.content_type)

    db_obj = AttachmentModel(
        file=key,
        content_type=file.content_type
    )
    session.add(db_obj)
    return db_obj


async def update_attachment(
        session: AsyncSession,
        attachment_id: UUID | str,
        file: UploadFile
) -> Type[AttachmentModel]:
    attachment = await get_attachment(session, attachment_id)

    filename = file.filename or "file"
    data = await file.read()
    key, _ = AttachmentService.build_storage_key(filename, file.content_type)
    await upload_bytes(key, data, content_type=file.content_type)

    attachment.file = key
    attachment.content_type = file.content_type
    return attachment


async def delete_attachment(session: AsyncSession, attachment_id: UUID | str) -> None:
    await session.delete(await get_attachment(session, attachment_id))
