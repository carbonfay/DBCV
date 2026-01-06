from uuid import UUID
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from datetime import datetime, timedelta
from app.config import settings

router = APIRouter()

source_path = "/attachment/{file_name}"


@router.get(
    f"{source_path}"
)
async def get_media_file(file_name: str):
    # Try S3 by key first
    try:
        from app.services.s3_service import object_exists, stream_object
        # Try flat key first (legacy)
        key = f"attachment/{file_name}"
        if await object_exists(key):
            iterator, headers = await stream_object(key)
            disposition = f"attachment; filename=\"{file_name}\""
            try:
                disposition += f"; filename*=UTF-8''{file_name}"
            except Exception:
                pass
            headers["Content-Disposition"] = disposition
            return StreamingResponse(iterator, media_type=headers.get("Content-Type", "application/octet-stream"), headers=headers)

        # Also try dated folders for recent 31 days
        today = datetime.utcnow().date()
        for days_ago in range(0, 31):
            d = today - timedelta(days=days_ago)
            dated_key = f"attachment/{d.strftime('%Y/%m/%d')}/{file_name}"
            if await object_exists(dated_key):
                iterator, headers = await stream_object(dated_key)
                disposition = f"attachment; filename=\"{file_name}\""
                try:
                    disposition += f"; filename*=UTF-8''{file_name}"
                except Exception:
                    pass
                headers["Content-Disposition"] = disposition
                return StreamingResponse(iterator, media_type=headers.get("Content-Type", "application/octet-stream"), headers=headers)
    except Exception:
        pass

    # Fallback to local filesystem for legacy
    file_path = Path("".join([str(settings.MEDIA_ROOT), source_path.format(file_name=file_name)]))
    if file_path.exists() and file_path.is_file():
        return FileResponse(path=file_path)
    raise HTTPException(
        status_code=404,
        detail="File not found.",
    )


# New: stream by full S3 key path, e.g.
# GET /media/attachment/2025/09/17/<random>.xlsx
@router.get("/{path:path}")
async def get_media_by_path(path: str):
    from app.services.s3_service import object_exists, stream_object
    # Normalize: allow missing 'attachment/' prefix
    normalized = path if path.startswith("attachment/") else f"attachment/{path}"

    # First try S3 by exact key
    if await object_exists(normalized):
        file_name = normalized.split('/')[-1]
        iterator, headers = await stream_object(normalized)
        disposition = f"attachment; filename=\"{file_name}\""
        try:
            disposition += f"; filename*=UTF-8''{file_name}"
        except Exception:
            pass
        headers["Content-Disposition"] = disposition
        return StreamingResponse(iterator, media_type=headers.get("Content-Type", "application/octet-stream"), headers=headers)

    # Fallback to local filesystem for legacy
    file_path = Path(str(settings.MEDIA_ROOT / normalized))
    if file_path.exists() and file_path.is_file():
        return FileResponse(path=file_path)
    raise HTTPException(status_code=404, detail="File not found.")


# Alternate access via query param for Swagger (slashes may be %-encoded)
@router.get("/")
async def get_media_by_key(key: str):
    from urllib.parse import unquote
    from app.services.s3_service import object_exists, stream_object
    raw_key = unquote(key)
    normalized = raw_key if raw_key.startswith("attachment/") else f"attachment/{raw_key}"
    if await object_exists(normalized):
        file_name = normalized.split('/')[-1]
        iterator, headers = await stream_object(normalized)
        disposition = f"attachment; filename=\"{file_name}\""
        try:
            disposition += f"; filename*=UTF-8''{file_name}"
        except Exception:
            pass
        headers["Content-Disposition"] = disposition
        return StreamingResponse(iterator, media_type=headers.get("Content-Type", "application/octet-stream"), headers=headers)
    raise HTTPException(status_code=404, detail="File not found.")