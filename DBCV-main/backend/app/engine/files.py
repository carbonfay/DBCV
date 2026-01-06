import io
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import mimetypes

from app.services.attachment_service import AttachmentService
from app.services.s3_storage_service import S3StorageService
from app.services.attachment_repository_sql import SqlAttachmentRepository
from app.database import sessionmanager


class FileCreatorException(Exception):
    pass


class FileCreator(ABC):
    @abstractmethod
    def create(self, data: Any) -> io.BytesIO:
        pass


class CSVFileCreator(FileCreator):
    def create(self, data: List[Dict[str, Any]]) -> io.BytesIO:
        b = io.BytesIO()
        if data:
            header = ",".join(data[0].keys()) + "\n"
            csv_data = header + "".join([",".join(str(value) for value in row.values()) + "\n" for row in data])
            b.write(csv_data.encode('utf-8'))
        b.seek(0)
        return b


class ExcelFileCreator(FileCreator):
    def create(self, data: List[Dict[str, Any]]) -> io.BytesIO:
        b = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        if data:
            header = list(data[0].keys())
            ws.append(header)
            for row in data:
                ws.append(list(row.values()))
        wb.save(b)
        b.seek(0)
        return b


class JSONFileCreator(FileCreator):
    def create(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> io.BytesIO:
        b = io.BytesIO()
        json_data = json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')
        b.write(json_data)
        b.seek(0)
        return b


class TXTFileCreator(FileCreator):
    def create(self, data: str) -> io.BytesIO:
        b = io.BytesIO()
        b.write(data.encode('utf-8'))
        b.seek(0)
        return b


class PDFFileCreator(FileCreator):
    def create(self, data: str) -> io.BytesIO:
        b = io.BytesIO()
        c = canvas.Canvas(b, pagesize=letter)
        c.drawString(100, 730, data)
        c.save()
        b.seek(0)
        return b


class FileCreatorFactory:
    @staticmethod
    def get_creator(file_type: str) -> FileCreator:
        creators = {
            "csv": CSVFileCreator(),
            "xlsx": ExcelFileCreator(),
            "json": JSONFileCreator(),
            "txt": TXTFileCreator(),
            "pdf": PDFFileCreator(),
        }
        return creators.get(file_type.lower(), None)


async def create_universal_file_attachment(session: AsyncSession, data: Any, file_type: str, filename: str = "file",
                                           service: AttachmentService | None = None) -> \
        Dict[str, Any]:
    creator = FileCreatorFactory.get_creator(file_type)
    if not creator:
        raise ValueError(f"Неподдерживаемый тип файла: {file_type}")

    b = creator.create(data)
    full_name = f"{filename}.{file_type}"
    guessed_type, _ = mimetypes.guess_type(full_name)
    content_type = guessed_type or {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv; charset=utf-8",
        "json": "application/json; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
        "pdf": "application/pdf",
    }.get(file_type.lower(), "application/octet-stream")

    if service is None:
        storage = S3StorageService()
        repo = SqlAttachmentRepository(sessionmanager.engine)
        service = AttachmentService(storage, repo)
    meta = await service.create_from_bytes(b.getvalue(), full_name, content_type)
    return {"id": meta.id, "content_type": meta.content_type, "file_name": meta.file_name,
            "size": meta.size, "url": f"{meta.id}"}
