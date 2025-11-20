from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, Tuple
from datetime import datetime
import re
import os
from uuid import uuid4


@dataclass
class AttachmentMeta:
    id: str
    content_type: Optional[str]
    key: str
    file_name: Optional[str] = None
    size: Optional[int] = None


class AttachmentStoragePort(Protocol):
    async def upload(self, key: str, data: bytes, content_type: Optional[str] = None) -> None: ...
    async def get_bytes(self, key: str) -> bytes: ...


class AttachmentRepository(Protocol):
    async def create(self, content_type: Optional[str], key: str, message_id: Optional[str] = None) -> AttachmentMeta: ...
    async def get_by_id(self, attachment_id: str) -> Optional[AttachmentMeta]: ...


class AttachmentService:
    def __init__(self, storage: AttachmentStoragePort, repo: AttachmentRepository) -> None:
        self.storage = storage
        self.repo = repo

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        base = os.path.basename(name)
        base = base.strip().replace(" ", "_")
        # keep letters, numbers, dot, dash, underscore
        base = re.sub(r"[^A-Za-z0-9._-]", "", base)
        # avoid empty
        return base or "file"

    @staticmethod
    def _ensure_ext(filename: str, content_type: Optional[str]) -> str:
        if "." in filename and not filename.endswith("."):
            return filename
        # fallback by content type if missing
        mapping = {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "text/csv": ".csv",
            "application/json": ".json",
            "text/plain": ".txt",
            "application/pdf": ".pdf",
        }
        ext = mapping.get(content_type or "", "")
        return filename + ext

    @staticmethod
    def _build_random_name(ext: str | None) -> Tuple[str, str]:
        """Return (key, random_filename). Filename is fully random; ext may be empty or like '.xlsx'."""
        now = datetime.utcnow()
        date_prefix = now.strftime("%Y/%m/%d")
        uniq = uuid4().hex
        ext = ext or ""
        if ext and not ext.startswith("."):
            ext = "." + ext
        random_filename = f"{uniq}{ext}"
        key = f"attachment/{date_prefix}/{random_filename}"
        return key, random_filename

    @classmethod
    def build_storage_key(cls, filename: str, content_type: Optional[str]) -> Tuple[str, str]:
        sanitized = cls._sanitize_filename(filename)
        sanitized = cls._ensure_ext(sanitized, content_type)
        ext = sanitized.rsplit('.', 1)[1] if '.' in sanitized else None
        return cls._build_random_name(ext)

    async def create_from_bytes(self, data: bytes, filename: str, content_type: Optional[str]) -> AttachmentMeta:
        key, unique_filename = self.build_storage_key(filename, content_type)
        await self.storage.upload(key, data, content_type=content_type)
        meta = await self.repo.create(content_type=content_type, key=key)
        meta.file_name = unique_filename
        meta.size = len(data)
        return meta

