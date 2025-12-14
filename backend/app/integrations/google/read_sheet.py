"""Google Sheets Read интеграция используя google-api-python-client библиотеку."""
from typing import Dict, Any
from uuid import UUID
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем библиотеку НАПРЯМУЮ в backend код
try:
    import google.auth
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    google = None
    service_account = None
    build = None


class GoogleSheetsReadIntegration(BaseIntegration):
    """Интеграция для чтения данных из Google Таблиц через Google Sheets API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_sheets_read",
            version="1.0.0",
            name="Google Sheets Read",
            description="Чтение данных из Google Таблиц через Google Sheets API",
            category="storage",
            icon_s3_key="icons/integrations/google-sheets.svg",
            color="#4285F4",
            config_schema={
                "type": "object",
                "required": ["spreadsheet_id", "range"],
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "title": "Spreadsheet ID",
                        "description": "ID таблицы Google Sheets (можно использовать переменные: {$bot.spreadsheet_id$})"
                    },
                    "range": {
                        "type": "string",
                        "title": "Range",
                        "description": "Диапазон ячеек для чтения (например, 'Лист1!A1:B10' или 'Лист1')"
                    }
                }
            },
            credentials_provider="google",
            credentials_strategy="oauth",
            library_name="google-api-python-client>=2.0.0" if GOOGLE_SHEETS_AVAILABLE else None,
            examples=[
                {
                    "title": "Чтение всего листа",
                    "config": {
                        "spreadsheet_id": "{$bot.spreadsheet_id$}",
                        "range": "Лист1"
                    }
                },
                {
                    "title": "Чтение определенного диапазона",
                    "config": {
                        "spreadsheet_id": "1aBcDeFgHiJkLmNoPqRsTuVwXyZ",
                        "range": "A1:B10"
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
        if not GOOGLE_SHEETS_AVAILABLE:
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
            provider="google",
            strategy="oauth"
        )

        if not creds:
            await logger.error("Google credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google credentials not found in credentials"
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
        spreadsheet_id = config.get("spreadsheet_id")
        range_name = config.get("range")

        if not spreadsheet_id or not range_name:
            await logger.error("spreadsheet_id and range are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "spreadsheet_id and range are required"
                }
            }

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем учетные данные из сервисного аккаунта
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )

            # Создаем сервис для работы с Google Sheets
            service = build('sheets', 'v4', credentials=credentials)

            # Выполняем запрос к API Google Sheets
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            
            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "spreadsheet_id": spreadsheet_id,
                        "range": range_name,
                        "values": values,
                        "found_rows": len(values)
                    }
                }
            }
        except Exception as e:
            await logger.error(f"Google Sheets API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

