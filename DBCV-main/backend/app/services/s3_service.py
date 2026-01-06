from typing import Optional

import aiobotocore.session
from aiobotocore.config import AioConfig

from app.config import settings
from datetime import datetime
from email.utils import format_datetime


aiobotocore_session = aiobotocore.session.AioSession()


async def upload_bytes(key: str, data: bytes, content_type: Optional[str] = None) -> None:
    async with aiobotocore_session.create_client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        config=AioConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        aws_secret_access_key=settings.S3_SECRET_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY,
    ) as s3_client:
        params = {"Bucket": settings.S3_BUCKET, "Key": key, "Body": data}
        if content_type:
            params["ContentType"] = content_type
        await s3_client.put_object(**params)


async def generate_presigned_get_url(key: str, expires_in: int = 3600) -> str:
    presign_endpoint = settings.S3_PUBLIC_ENDPOINT or settings.S3_ENDPOINT
    async with aiobotocore_session.create_client(
        "s3",
        endpoint_url=presign_endpoint,
        region_name=settings.S3_REGION,
        config=AioConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        aws_secret_access_key=settings.S3_SECRET_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY,
    ) as s3_client:
        return await s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )


async def object_exists(key: str) -> bool:
    async with aiobotocore_session.create_client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        config=AioConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        aws_secret_access_key=settings.S3_SECRET_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY,
    ) as s3_client:
        try:
            await s3_client.head_object(Bucket=settings.S3_BUCKET, Key=key)
            return True
        except Exception:
            return False


async def stream_object(key: str, chunk_size: int = 1024 * 1024):
    """Return async iterator over object bytes and response metadata headers.

    Uses HEAD to fetch headers first, then streams via GET in a safe async context.
    """
    # Fetch headers via HEAD
    async with aiobotocore_session.create_client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        config=AioConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        aws_secret_access_key=settings.S3_SECRET_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY,
    ) as head_client:
        head = await head_client.head_object(Bucket=settings.S3_BUCKET, Key=key)

    headers = {
        "Content-Length": str(head.get("ContentLength", "")),
        "Content-Type": head.get("ContentType", "application/octet-stream"),
    }
    etag = head.get("ETag")
    if etag:
        headers["ETag"] = etag
    last_modified = head.get("LastModified")
    if isinstance(last_modified, datetime):
        try:
            headers["Last-Modified"] = format_datetime(last_modified, usegmt=True)
        except Exception:
            pass

    async def iterator():
        async with aiobotocore_session.create_client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            region_name=settings.S3_REGION,
            config=AioConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
            aws_secret_access_key=settings.S3_SECRET_KEY,
            aws_access_key_id=settings.S3_ACCESS_KEY,
        ) as s3_client:
            resp = await s3_client.get_object(Bucket=settings.S3_BUCKET, Key=key)
            body = resp["Body"]
            try:
                while True:
                    chunk = await body.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            finally:
                # body.close may be sync in some transports
                try:
                    close_result = body.close()
                    if close_result is not None:
                        # Some implementations return awaitable
                        try:
                            await close_result  # type: ignore
                        except TypeError:
                            pass
                except Exception:
                    pass

    return iterator(), headers


async def get_object_bytes(key: str) -> tuple[bytes, dict]:
    """Download full object into memory and return (bytes, headers). Suitable for small-to-medium files."""
    async with aiobotocore_session.create_client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        config=AioConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        aws_secret_access_key=settings.S3_SECRET_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY,
    ) as s3_client:
        resp = await s3_client.get_object(Bucket=settings.S3_BUCKET, Key=key)
        body = resp["Body"]
        data = await body.read()
        try:
            close_result = body.close()
            if close_result is not None:
                try:
                    await close_result  # type: ignore
                except TypeError:
                    pass
        except Exception:
            pass
        headers = {
            "Content-Length": str(resp.get("ContentLength", "")),
            "Content-Type": resp.get("ContentType", "application/octet-stream"),
        }
        etag = resp.get("ETag")
        if etag:
            headers["ETag"] = etag
        last_modified = resp.get("LastModified")
        if isinstance(last_modified, datetime):
            try:
                headers["Last-Modified"] = format_datetime(last_modified, usegmt=True)
            except Exception:
                pass
        return data, headers


