"""Сервис для работы с иконками в S3."""
from typing import Optional
from app.services.s3_service import upload_bytes, generate_presigned_get_url, object_exists
from app.config import settings


class IconService:
    """Сервис для работы с иконками в S3."""
    
    def __init__(self):
        self.bucket = settings.S3_BUCKET
        self.base_path = "icons"
    
    async def get_icon_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Получает публичный URL иконки из S3.
        
        Args:
            s3_key: S3 ключ иконки
            expires_in: Время жизни URL в секундах
        
        Returns:
            Публичный URL иконки
        """
        # Проверяем существование
        if not await object_exists(s3_key):
            # Возвращаем placeholder или дефолтную иконку
            return f"{settings.S3_PUBLIC_ENDPOINT}/{self.bucket}/icons/default.svg"
        
        # Генерируем presigned URL
        return await generate_presigned_get_url(s3_key, expires_in=expires_in)
    
    async def upload_icon(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "image/svg+xml"
    ) -> str:
        """
        Загружает иконку в S3 и возвращает ключ.
        
        Args:
            file_content: Содержимое файла
            filename: Имя файла (будет добавлен base_path)
            content_type: MIME тип файла
        
        Returns:
            S3 ключ загруженной иконки
        """
        s3_key = f"{self.base_path}/{filename}"
        await upload_bytes(s3_key, file_content, content_type=content_type)
        return s3_key
    
    async def icon_exists(self, s3_key: str) -> bool:
        """
        Проверяет существование иконки в S3.
        
        Args:
            s3_key: S3 ключ иконки
        
        Returns:
            True если иконка существует
        """
        return await object_exists(s3_key)


# Глобальный экземпляр сервиса
icon_service = IconService()

