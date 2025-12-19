"""Google Drive File Upload интеграция используя google-api-python-client библиотеку."""
from typing import Dict, Any
from uuid import UUID
import json
import base64

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import google.auth
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2 import service_account
    from googleapiclient.errors import HttpError
    import io
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    google = None
    service_account = None
    build = None
    HttpError = Exception
    io = None


class GoogleDriveFileUploadIntegration(BaseIntegration):
    """Интеграция для загрузки файлов в Google Drive через Google Drive API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_drive_file_upload",
            version="1.0.0",
            name="Google Drive File Upload",
            description="Загрузка файлов в Google Drive через Google Drive API",
            category="storage",
            icon_s3_key="icons/integrations/google-drive.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "required": ["file_content", "file_name"],
                "properties": {
                    "file_content": {
                        "type": "string",
                        "title": "File Content",
                        "description": "Содержимое файла для загрузки (в base64 или текстом)"
                    },
                    "file_name": {
                        "type": "string",
                        "title": "File Name",
                        "description": "Имя файла в Google Drive"
                    },
                    "file_type": {
                        "type": "string",
                        "title": "File Type (MIME)",
                        "description": "MIME тип файла (автоопределение если не указано)",
                        "default": "text/plain"
                    },
                    "parent_folder_id": {
                        "type": "string",
                        "title": "Parent Folder ID",
                        "description": "ID папки для загрузки файла (по умолчанию корневая директория)"
                    }
                }
            },
            credentials_provider="google_drive",
            credentials_strategy="oauth",
            library_name="google-api-python-client>=2.0.0" if GOOGLE_DRIVE_AVAILABLE else None,
            examples=[
                {
                    "title": "Загрузка текстового файла",
                    "config": {
                        "file_content": "{$session.data$}",
                        "file_name": "user_data.txt",
                        "file_type": "text/plain"
                    }
                },
                {
                    "title": "Загрузка документа",
                    "config": {
                        "file_content": "{$session.document_content$}",
                        "file_name": "report.docx",
                        "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
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
        Выполняет интеграцию используя библиотеку google-api-python-client.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not GOOGLE_DRIVE_AVAILABLE:
            await logger.error("google-api-python-client library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "google-api-python-client library is not installed"
                }
            }

        # Получаем учетные данные из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="google_drive",
            strategy="oauth"
        )

        if not creds:
            await logger.error("Google Drive credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google Drive credentials not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        # Проверяем, есть ли в payload JSON ключи от сервисного аккаунта
        service_account_info = payload.get("service_account_info")
        if not service_account_info:
            # Если service_account_info нет, может быть строкой JSON
            service_account_json = payload.get("service_account_json")
            if service_account_json and isinstance(service_account_json, str):
                try:
                    service_account_info = json.loads(service_account_json)
                except json.JSONDecodeError:
                    await logger.error("Invalid JSON in service account info")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 401,
                            "description": "Invalid service account JSON in credentials"
                        }
                    }

        if not service_account_info:
            await logger.error(f"Service account info not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Service account info not found in credentials"
                }
            }

        # Получаем параметры из config
        file_content = config.get("file_content")
        file_name = config.get("file_name")
        file_type = config.get("file_type", "text/plain")
        parent_folder_id = config.get("parent_folder_id")

        if not file_content or not file_name:
            await logger.error("file_content and file_name are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "file_content and file_name are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем учетные данные из сервисного аккаунта
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/drive"]
            )

            # Создаем сервис для работы с Google Drive
            service = build('drive', 'v3', credentials=credentials)

            # Определяем, является ли содержимое base64
            try:
                content_bytes = base64.b64decode(file_content)
            except Exception:
                # Если не base64, то сохраняем как текст
                content_bytes = file_content.encode('utf-8')

            # Создаем объект файла в памяти
            file_io = io.BytesIO(content_bytes)

            # Подготовим метаданные файла
            file_metadata = {
                'name': file_name
            }

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            # Создаем медиа-объект для загрузки
            media = MediaIoBaseUpload(file_io, mimetype=file_type, resumable=True)

            # Загружаем файл
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, webViewLink, webContentLink'
            ).execute()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": file.get('id'),
                        "name": file.get('name'),
                        "mimeType": file.get('mimeType'),
                        "size": file.get('size'),
                        "webViewLink": file.get('webViewLink'),
                        "webContentLink": file.get('webContentLink')
                    }
                }
            }
        except HttpError as e:
            await logger.error(f"Google Drive API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.resp.status if hasattr(e, 'resp') and hasattr(e.resp, 'status') else 500,
                    "description": f"Google Drive API error: {str(e)}"
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

