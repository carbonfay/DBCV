"""Dropbox File Upload интеграция используя dropbox библиотеку."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import dropbox
    from dropbox.files import WriteMode
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False
    dropbox = None
    WriteMode = None


class DropboxFileUploadIntegration(BaseIntegration):
    """Интеграция для загрузки файлов в Dropbox."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="dropbox_file_upload",
            version="1.0.0",
            name="Dropbox File Upload",
            description="Загрузка файлов в Dropbox через Dropbox API",
            category="storage",
            icon_s3_key="icons/integrations/dropbox.svg",
            color="#0061FF",
            config_schema={
                "type": "object",
                "required": ["file_path", "file_content"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "title": "File Path",
                        "description": "Путь для сохранения файла в Dropbox (например, '/folder/myfile.txt')"
                    },
                    "file_content": {
                        "type": "string",
                        "title": "File Content",
                        "description": "Содержимое файла для загрузки"
                    },
                    "mode": {
                        "type": "string",
                        "title": "Write Mode",
                        "description": "Режим записи файла",
                        "enum": ["add", "overwrite"],
                        "default": "add"
                    }
                }
            },
            credentials_provider="dropbox",
            credentials_strategy="api_key",  # Dropbox uses access tokens
            library_name="dropbox>=11.36.0" if DROPBOX_AVAILABLE else None,
            examples=[
                {
                    "title": "Загрузка текстового файла",
                    "config": {
                        "file_path": "/uploads/user_data.txt",
                        "file_content": "{$session.user_data$}",
                        "mode": "overwrite"
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя библиотеку dropbox.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not DROPBOX_AVAILABLE:
            await logger.error("dropbox library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "dropbox library is not installed"
                }
            }

        # Получаем access token из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="dropbox",
            strategy="api_key"
        )

        if not creds:
            await logger.error("Dropbox credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Dropbox access token not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        access_token = payload.get("access_token") or payload.get("api_key") or payload.get("token")
        if not access_token:
            await logger.error(f"Access token not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Access token not found in credentials"
                }
            }

        # Получаем параметры из config
        file_path = config.get("file_path")
        file_content = config.get("file_content")
        mode = config.get("mode", "add")

        if not file_path or not file_content:
            await logger.error("file_path and file_content are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "file_path and file_content are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем клиент Dropbox
            dbx = dropbox.Dropbox(access_token)

            # Определяем режим записи
            write_mode = WriteMode.overwrite if mode == "overwrite" else WriteMode.add

            # Загружаем файл (file_content как байты)
            file_bytes = file_content.encode('utf-8')
            
            result = dbx.files_upload(
                file_bytes,
                file_path,
                mode=write_mode,
                autorename=True,  # Переименовать автоматически при конфликтах
                mute=True  # Не отправлять уведомления
            )

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": result.id,
                        "name": result.name,
                        "path_display": result.path_display,
                        "size": result.size,
                        "client_modified": result.client_modified.isoformat() if result.client_modified else None,
                        "server_modified": result.server_modified.isoformat() if result.server_modified else None
                    }
                }
            }
        except dropbox.exceptions.ApiError as e:
            await logger.error(f"Dropbox API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Dropbox API error: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

