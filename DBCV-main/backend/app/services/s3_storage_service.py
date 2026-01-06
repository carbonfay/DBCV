from __future__ import annotations

from typing import Optional
from aiobotocore.config import AioConfig
import aiobotocore.session

from app.config import settings
from app.services.attachment_service import AttachmentStoragePort


aiobotocore_session = aiobotocore.session.AioSession()


class S3StorageService(AttachmentStoragePort):
    async def upload(self, key: str, data: bytes, content_type: Optional[str] = None) -> None:
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

    async def get_bytes(self, key: str) -> bytes:
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
            return data


