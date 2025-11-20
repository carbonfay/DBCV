from __future__ import annotations

from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection

from app.services.attachment_service import AttachmentRepository, AttachmentMeta


class SqlAttachmentRepository(AttachmentRepository):
    def __init__(self, engine: AsyncEngine | AsyncConnection) -> None:
        self.engine = engine

    async def create(self, content_type: Optional[str], key: str, message_id: Optional[str] = None) -> AttachmentMeta:
        from uuid import uuid4
        attachment_id = str(uuid4())
        if hasattr(self.engine, "connect"):
            async with self.engine.connect() as conn:  # type: ignore[attr-defined]
                row = (await conn.execute(text(
                    """
                    INSERT INTO attachment (id, content_type, file, message_id, created_at, updated_at)
                    VALUES (:id, :content_type, :file, :message_id, NOW(), NOW())
                    RETURNING id, content_type, file
                    """
                ), {"id": attachment_id, "content_type": content_type, "file": key, "message_id": message_id})).mappings().first()
                await conn.commit()
        else:
            conn = self.engine  # type: ignore[assignment]
            row = (await conn.execute(text(
                """
                INSERT INTO attachment (id, content_type, file, message_id, created_at, updated_at)
                VALUES (:id, :content_type, :file, :message_id, NOW(), NOW())
                RETURNING id, content_type, file
                """
            ), {"id": attachment_id, "content_type": content_type, "file": key, "message_id": message_id})).mappings().first()
            await conn.commit()
        data = dict(row)
        return AttachmentMeta(id=data["id"], content_type=data.get("content_type"), key=data.get("file"))

    async def get_by_id(self, attachment_id: str) -> Optional[AttachmentMeta]:
        if hasattr(self.engine, "connect"):
            async with self.engine.connect() as conn:  # type: ignore[attr-defined]
                row = (await conn.execute(text(
                    "SELECT id, content_type, file FROM attachment WHERE id = :id"
                ), {"id": attachment_id})).mappings().first()
        else:
            conn = self.engine  # type: ignore[assignment]
            row = (await conn.execute(text(
                "SELECT id, content_type, file FROM attachment WHERE id = :id"
            ), {"id": attachment_id})).mappings().first()
        if not row:
            return None
        data = dict(row)
        return AttachmentMeta(id=data["id"], content_type=data.get("content_type"), key=data.get("file"))


