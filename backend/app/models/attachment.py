import pathlib
import uuid
import os.path
from typing import Optional, List, Union, Any
from sqlalchemy import ForeignKey, Column, Dialect
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from app.config import settings
from sqlalchemy import String
import random, string


def random_filename(file_ext):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.' + file_ext


class FileType(String):
    pass


class AttachmentModel(BaseModel):
    __tablename__ = "attachment"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    content_type: Mapped[str | None]
    # Stores S3 object key, e.g., "attachment/<random>.<ext>"
    file = Column(FileType)

    message_id: Mapped[UUID] = mapped_column(ForeignKey("message.id"), nullable=True)
    message: Mapped["MessageModel"] = relationship("MessageModel", back_populates="attachments", foreign_keys=message_id, lazy="select", )

    @property
    def url(self):
        # Direct media path by stored S3 key
        try:
            key = str(self.file)
            if key.startswith("attachment/"):
                return f"/{settings.MEDIA_URL}/{key}"
        except Exception:
            pass
        return f"{settings.API_V1_STR}/attachments/download?attachment_id={self.id}"

    @property
    def file_name(self) -> str | None:
        if self.file is None:
            return
        try:
            return str(self.file).split('/')[-1]
        except Exception:
            return None

    @property
    def size(self):
        try:
            return self.file.size
        except Exception:
            return 0

    @property
    def path(self):
        return None

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, name={self.file_name!r})"

    def __repr__(self):
        return str(self)

    def get_dict(self):
        return {"id": str(self.id),
                "content_type": self.content_type,
                "file_name": self.file_name,
                "size": self.size,
                "url": self.url}

