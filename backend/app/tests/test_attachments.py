
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.engine.files import create_universal_file_attachment
from app.services.attachment_service import AttachmentService, AttachmentStoragePort
from app.services.attachment_repository_sql import SqlAttachmentRepository
from app.models.attachment import AttachmentModel


class FakeStorage(AttachmentStoragePort):
    def __init__(self):
        self._store: dict[str, bytes] = {}

    async def upload(self, key: str, data: bytes, content_type: str | None = None) -> None:
        self._store[key] = data

    async def get_bytes(self, key: str) -> bytes:
        return self._store[key]


@pytest.mark.asyncio
async def test_create_universal_file_attachment_inserts_record_and_uploads():
    # Local isolated in-memory DB (sqlite) to avoid external Postgres tools
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        # Create only the attachment table to avoid creating PG-specific tables in SQLite
        await conn.run_sync(lambda sync_conn: AttachmentModel.__table__.create(sync_conn))
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Arrange: in-memory CSV
        rows = [
            {"col1": "a", "col2": 1},
            {"col1": "b", "col2": 2},
        ]
        filename = "testfile"
        file_type = "csv"

        storage = FakeStorage()
        repo = SqlAttachmentRepository(session.bind)
        service = AttachmentService(storage, repo)

        # Act
        result = await create_universal_file_attachment(
            session=session,
            data=rows,
            file_type=file_type,
            filename=filename,
            service=service,
        )

        # Assert result shape
        assert result.get("id") is not None
        att_id = result["id"]
        file_name = result.get("file_name")
        assert file_name is not None
        assert file_name.endswith(f".{file_type}")

        # Assert DB row exists and key matches
        row = (await session.execute(text("SELECT id, content_type, file FROM attachment WHERE id = :id"), {"id": att_id})).mappings().first()
        assert row is not None
        key = row["file"]
        assert key.startswith("attachment/")
        parts = key.split('/')
        assert len(parts) == 5
        year, month, day = parts[1:4]
        assert len(year) == 4 and year.isdigit()
        assert len(month) == 2 and month.isdigit()
        assert len(day) == 2 and day.isdigit()
        assert parts[-1] == file_name

        # Fake storage contains data
        data = await storage.get_bytes(row["file"])
        assert isinstance(data, (bytes, bytearray)) and len(data) > 0
