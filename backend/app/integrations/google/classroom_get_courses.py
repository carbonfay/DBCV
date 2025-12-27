"""Google Classroom Get Courses интеграция для получения списка курсов."""
from typing import Dict, Any
from uuid import UUID
import google.auth.transport.requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.exceptions import GoogleAuthError

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Проверяем доступность библиотеки
try:
    import googleapiclient
    GOOGLE_API_CLIENT_AVAILABLE = True
except ImportError:
    GOOGLE_API_CLIENT_AVAILABLE = False
    googleapiclient = None


class GoogleClassroomGetCoursesIntegration(BaseIntegration):
    """Интеграция для получения списка курсов из Google Classroom."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_classroom_get_courses",
            version="1.0.0",
            name="Google Classroom Get Courses",
            description="Получение списка курсов из Google Classroom",
            category="education",
            icon_s3_key="icons/integrations/google_classroom.svg",
            color="#4285f4",
            config_schema={
                "type": "object",
                "required": [],
                "properties": {
                    "course_states": {
                        "type": "array",
                        "title": "Course States",
                        "description": "Фильтр по состоянию курса",
                        "items": {
                            "type": "string",
                            "enum": ["COURSE_STATE_UNSPECIFIED", "ACTIVE", "ARCHIVED", "PROVISIONED", "DECLINED", "SUSPENDED"]
                        },
                        "default": ["ACTIVE"]
                    },
                    "teacher_id": {
                        "type": "string",
                        "title": "Teacher ID",
                        "description": "Фильтр по преподавателю (ID пользователя или 'me')"
                    },
                    "student_id": {
                        "type": "string",
                        "title": "Student ID",
                        "description": "Фильтр по студенту (ID пользователя или 'me')"
                    },
                    "page_size": {
                        "type": "integer",
                        "title": "Page Size",
                        "description": "Количество результатов на странице",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    }
                }
            },
            credentials_provider="google",
            credentials_strategy="service_account",  # или "oauth" - будет обрабатываться в execute
            library_name="google-api-python-client>=2.0",
            examples=[
                {
                    "title": "Получить активные курсы",
                    "config": {
                        "course_states": ["ACTIVE"]
                    }
                },
                {
                    "title": "Получить курсы преподавателя",
                    "config": {
                        "teacher_id": "me"
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
            strategy=None  # Попробуем получить любые Google credentials
        )

        if not creds:
            await logger.error("Google credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google credentials not found"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            payload = creds

        # Определяем тип credentials (service_account или oauth)
        credentials_type = payload.get("type")  # service_account обычно имеет "type": "service_account"

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
                credentials = service_account.Credentials.from_service_account_info(
                    info,
                    scopes=["https://www.googleapis.com/auth/classroom.courses.readonly"]
                )
            else:
                # Для OAuth предполагаем, что в payload есть access_token
                # или что payload содержит полный OAuth-объект (как refresh_token, client_id и т.д.)
                # В реальной системе вам может понадобиться более сложная логика для обновления токена
                access_token = payload.get("access_token")
                if not access_token:
                    await logger.error("Access token not found in OAuth credentials")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 401,
                            "description": "Access token not found in OAuth credentials"
                        }
                    }

                # Для OAuth токена создание credentials может отличаться
                # и зависеть от вашей системы управления токенами
                # Этот пример показывает базовый подход, но в реальности
                # вы можете использовать уже готовый объект credentials из вашей системы
                # или создать его через google.oauth2.credentials.Credentials
                from google.oauth2.credentials import Credentials
                credentials = Credentials(token=access_token)

        except (ValueError, KeyError) as e:
            await logger.error(f"Error creating Google credentials: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Invalid Google credentials: {str(e)}"
                }
            }
        except GoogleAuthError as e:
            await logger.error(f"Google Auth error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": f"Google authentication error: {str(e)}"
                }
            }

        # Проверяем валидность credentials перед созданием сервиса
        if not credentials.valid:
            try:
                request = google.auth.transport.requests.Request()
                credentials.refresh(request)
            except GoogleAuthError as e:
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

        # Подготовим параметры для запроса
        params = {}

        # Добавляем фильтры из config
        course_states = config.get("course_states")
        if course_states:
            params["courseStates"] = course_states

        teacher_id = config.get("teacher_id")
        if teacher_id:
            params["teacherId"] = teacher_id

        student_id = config.get("student_id")
        if student_id:
            params["studentId"] = student_id

        page_size = config.get("page_size")
        if page_size:
            params["pageSize"] = page_size

        # Выполняем запрос к Google Classroom API
        try:
            # Выполняем API-вызов
            results = service.courses().list(**params).execute()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": results
                }
            }

        except Exception as e:
            await logger.error(f"Google Classroom API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"Google Classroom API error: {str(e)}"
                }
            }
