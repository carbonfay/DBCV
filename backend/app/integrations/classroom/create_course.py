"""Google Classroom Create Course интеграция используя google-api-python-client библиотеку."""
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
    from googleapiclient.errors import HttpError
    GOOGLE_CLASSROOM_AVAILABLE = True
except ImportError:
    GOOGLE_CLASSROOM_AVAILABLE = False
    google = None
    service_account = None
    build = None
    HttpError = Exception


class GoogleClassroomCreateCourseIntegration(BaseIntegration):
    """Интеграция для создания курса в Google Classroom через Google Classroom API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_classroom_create_course",
            version="1.0.0",
            name="Google Classroom Create Course",
            description="Создание курса в Google Classroom через Classroom API",
            category="education",
            icon_s3_key="icons/integrations/google-classroom.svg",
            color="#0D87E4",
            config_schema={
                "type": "object",
                "required": ["name", "courseState"],
                "properties": {
                    "name": {
                        "type": "string",
                        "title": "Course Name",
                        "description": "Название курса"
                    },
                    "section": {
                        "type": "string",
                        "title": "Section",
                        "description": "Раздел курса"
                    },
                    "description_heading": {
                        "type": "string",
                        "title": "Description Heading",
                        "description": "Заголовок описания"
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Полное описание курса"
                    },
                    "room": {
                        "type": "string",
                        "title": "Room",
                        "description": "Номер аудитории/комнаты"
                    },
                    "owner_id": {
                        "type": "string",
                        "title": "Owner ID",
                        "description": "ID владельца курса (учителя)"
                    },
                    "courseState": {
                        "type": "string",
                        "title": "Course State",
                        "description": "Состояние курса",
                        "enum": ["PROVISIONED", "ACTIVE", "ARCHIVED"],
                        "default": "ACTIVE"
                    },
                    "enrollmentCode": {
                        "type": "string",
                        "title": "Enrollment Code",
                        "description": "Код для регистрации студентов"
                    },
                    "teacherGroupEmail": {
                        "type": "string",
                        "title": "Teacher Group Email",
                        "description": "Email группы учителей"
                    },
                    "studentGroupEmail": {
                        "type": "string",
                        "title": "Student Group Email",
                        "description": "Email группы студентов"
                    },
                    "courseMaterialSets": {
                        "type": "array",
                        "title": "Course Material Sets",
                        "description": "Наборы материалов курса",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "title": "Title",
                                    "description": "Название набора материалов"
                                },
                                "material": {
                                    "type": "array",
                                    "title": "Material",
                                    "description": "Материалы",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "driveFile": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "string",
                                                        "title": "Drive File ID",
                                                        "description": "ID файла в Google Drive"
                                                    }
                                                }
                                            },
                                            "youtubeVideo": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "string",
                                                        "title": "YouTube Video ID",
                                                        "description": "ID видео на YouTube"
                                                    }
                                                }
                                            },
                                            "link": {
                                                "type": "object",
                                                "properties": {
                                                    "url": {
                                                        "type": "string",
                                                        "title": "URL",
                                                        "description": "Ссылка на внешний ресурс"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            credentials_provider="google_classroom",
            credentials_strategy="oauth",
            library_name="google-api-python-client>=2.0.0" if GOOGLE_CLASSROOM_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать активный курс",
                    "config": {
                        "name": "Информатика 101",
                        "section": "Основы программирования",
                        "description": "Введение в основы программирования",
                        "room": "Кабинет 201",
                        "courseState": "ACTIVE"
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
        if not GOOGLE_CLASSROOM_AVAILABLE:
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
            provider="google_classroom",
            strategy="oauth"
        )

        if not creds:
            await logger.error("Google Classroom credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Google Classroom credentials not found in credentials"
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

        # ИСПОЛЬЗУЕМ БИБЛИОТЕКУ НАПРЯМУЮ
        try:
            # Создаем учетные данные из сервисного аккаунта
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/classroom.courses",
                        "https://www.googleapis.com/auth/classroom.rosters",
                        "https://www.googleapis.com/auth/classroom.profile.emails",
                        "https://www.googleapis.com/auth/classroom.profile.photos"]
            )

            # Создаем сервис для работы с Google Classroom
            service = build('classroom', 'v1', credentials=credentials)

            # Подготовим тело запроса для создания курса
            course_body = {}
            for key, value in config.items():
                if key in ['name', 'section', 'description_heading', 'description', 'room', 'owner_id', 'courseState', 'enrollmentCode', 'teacherGroupEmail', 'studentGroupEmail', 'courseMaterialSets']:
                    course_body[key] = value

            # Создаем курс
            created_course = service.courses().create(body=course_body).execute()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "id": created_course['id'],
                        "name": created_course['name'],
                        "section": created_course.get('section', ''),
                        "description_heading": created_course.get('descriptionHeading', ''),
                        "description": created_course.get('description', ''),
                        "room": created_course.get('room', ''),
                        "owner_id": created_course['ownerId'],
                        "creation_time": created_course.get('creationTime', ''),
                        "update_time": created_course.get('updateTime', ''),
                        "enrollment_code": created_course.get('enrollmentCode', ''),
                        "course_state": created_course['courseState'],
                        "teacher_group_email": created_course.get('teacherGroupEmail', ''),
                        "student_group_email": created_course.get('studentGroupEmail', ''),
                        "alternate_link": created_course.get('alternateLink', ''),
                        "teacher_folder": created_course.get('teacherFolder', {}),
                        "course_group_email": created_course.get('courseGroupEmail', ''),
                        "guardians_enabled": created_course.get('guardiansEnabled', False)
                    }
                }
            }
        except HttpError as e:
            await logger.error(f"Google Classroom API error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": e.resp.status if hasattr(e, 'resp') and hasattr(e.resp, 'status') else 500,
                    "description": f"Google Classroom API error: {str(e)}"
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

