"""Google Classroom Create Course интеграция для создания нового курса."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Проверяем доступность библиотеки
try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2.service_account import Credentials as SvcAccountCredentials
    GOOGLE_API_CLIENT_AVAILABLE = True
except ImportError:
    GOOGLE_API_CLIENT_AVAILABLE = False
    googleapiclient = None
    build = None
    Request = None
    Credentials = None
    SvcAccountCredentials = None


class GoogleClassroomCreateCourseIntegration(BaseIntegration):
    """Интеграция для создания нового курса в Google Classroom."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_classroom_create_course",
            version="1.0.0",
            name="Google Classroom Create Course",
            description="Создание нового курса в Google Classroom",
            category="education",
            icon_s3_key="icons/integrations/google_classroom.svg",
            color="#4285f4",
            config_schema={
                "type": "object",
                "required": ["name", "owner_id"],
                "properties": {
                    "name": {
                        "type": "string",
                        "title": "Course Name",
                        "description": "Название курса"
                    },
                    "section": {
                        "type": "string",
                        "title": "Section",
                        "description": "Раздел или группа курса"
                    },
                    "description_heading": {
                        "type": "string",
                        "title": "Description Heading",
                        "description": "Заголовок описания курса"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Полное описание курса"
                    },
                    "room": {
                        "type": "string",
                        "title": "Room",
                        "description": "Номер аудитории"
                    },
                    "owner_id": {
                        "type": "string",
                        "title": "Owner ID",
                        "description": "ID преподавателя (обычно 'me' или email)"
                    },
                    "course_state": {
                        "type": "string",
                        "title": "Course State",
                        "enum": ["COURSE_STATE_UNSPECIFIED", "ACTIVE", "ARCHIVED", "PROVISIONED", "DECLINED", "SUSPENDED"],
                        "default": "PROVISIONED"
                    }
                }
            },
            credentials_provider="google",
            credentials_strategy="service_account",  # или "oauth" - будет обрабатываться в execute
            library_name="google-api-python-client>=2.0",
            examples=[
                {
                    "title": "Создать активный курс",
                    "config": {
                        "name": "Математика 101",
                        "owner_id": "me",
                        "course_state": "ACTIVE",
                        "description": "Основы высшей математики"
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
        if not GOOGLE_API_CLIENT_AVAILABLE:
            await logger.error("google-api-python-client library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "google-api-python-client library is not installed"
                }
            }

        # Получаем credentials из резолвера
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="google",
            strategy=None  # Провайдер сам определит стратегию
        )

        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        if not creds:
            await logger.error("Google credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google credentials not found"
                }
            }

        credentials_type = payload.get("type")

        try:
            if credentials_type == "service_account":
                # Используем service account credentials
                info = {
                    "type": payload.get("type"),
                    "project_id": payload.get("project_id"),
                    "private_key_id": payload.get("private_key_id"),
                    "private_key": payload.get("private_key"),
                    "client_email": payload.get("client_email"),
                    "client_id": payload.get("client_id"),
                    "auth_uri": payload.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                    "token_uri": payload.get("token_uri", "https://oauth2.googleapis.com/token"),
                    "auth_provider_x509_cert_url": payload.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
                    "client_x509_cert_url": payload.get("client_x509_cert_url"),
                    "universe_domain": payload.get("universe_domain", "googleapis.com")
                }

                # Создаем credentials объект для service account
                credentials = SvcAccountCredentials.from_service_account_info(
                    info,
                    scopes=["https://www.googleapis.com/auth/classroom.courses"]
                )
            else:
                # Для OAuth используем объект Credentials с необходимыми полями
                access_token = payload.get("access_token")
                refresh_token = payload.get("refresh_token")
                client_id = payload.get("client_id")
                client_secret = payload.get("client_secret")
                token_uri = payload.get("token_uri", "https://oauth2.googleapis.com/token")

                if not all([access_token, refresh_token, client_id, client_secret]):
                    await logger.error("Missing required OAuth fields (refresh_token, client_id, client_secret)")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 401,
                            "description": "Missing required OAuth fields (refresh_token, client_id, client_secret)"
                        }
                    }

                # Создаем объект Credentials с необходимыми полями для обновления
                credentials = Credentials(
                    token=access_token,
                    refresh_token=refresh_token,
                    token_uri=token_uri,
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=["https://www.googleapis.com/auth/classroom.courses"]
                )

        except (ValueError, KeyError) as e:
            await logger.error(f"Error creating Google credentials: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Invalid Google credentials: {str(e)}"
                }
            }

        # Проверяем валидность credentials перед созданием сервиса
        if not credentials.valid:
            try:
                request = Request()
                credentials.refresh(request)
            except Exception as e:
                await logger.error(f"Failed to refresh credentials: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": f"Failed to refresh credentials: {str(e)}"
                    }
                }

        # Создаем сервис Google Classroom
        try:
            service = build('classroom', 'v1', credentials=credentials)
        except Exception as e:
            await logger.error(f"Failed to build Google Classroom service: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Failed to build Google Classroom service: {str(e)}"
                }
            }

        # Подготовим тело запроса из config
        course_body = {}

        # Обязательные поля
        name = config.get("name")
        owner_id = config.get("owner_id")

        if not name or not owner_id:
            await logger.error("Name and owner_id are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "Name and owner_id are required"
                }
            }

        course_body["name"] = name
        course_body["ownerId"] = owner_id

        # Добавляем опциональные поля из config
        if "section" in config:
            course_body["section"] = config["section"]
        if "description_heading" in config:
            course_body["descriptionHeading"] = config["description_heading"]
        if "description" in config:
            course_body["description"] = config["description"]
        if "room" in config:
            course_body["room"] = config["room"]
        if "course_state" in config:
            course_body["courseState"] = config["course_state"]

        # Выполняем запрос к Google Classroom API для создания курса
        try:
            # Выполняем API-вызов
            result = service.courses().create(body=course_body).execute()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": result
                }
            }

        except Exception as e:
            await logger.error(f"Google Classroom API error during course creation: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Google Classroom API error during course creation: {str(e)}"
                }
            }
