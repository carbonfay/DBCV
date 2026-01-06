from typing import Annotated, AsyncIterator, TYPE_CHECKING

import aiobotocore.session
from aiobotocore.client import AioBaseClient
from aiobotocore.config import AioConfig
from fastapi import Depends
from app.config import settings

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
else:
    S3Client = object

aiobotocore_session = aiobotocore.session.AioSession()


async def get_s3_client() -> AsyncIterator[AioBaseClient]:
    async with aiobotocore_session.create_client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            region_name=settings.S3_REGION,
            config=AioConfig(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            ),
            aws_secret_access_key=settings.S3_SECRET_KEY,
            aws_access_key_id=settings.S3_ACCESS_KEY
    ) as s3_client:
        try:
            yield s3_client
        finally:
            await s3_client.close()


S3ClientDep = Annotated[S3Client, Depends(get_s3_client)]