"""Google Classroom Grade Submission интеграция используя google-api-python-client библиотеку."""
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


class GoogleClassroomSubmitGradeIntegration(BaseIntegration):
    """Интеграция для отправки оценок в Google Classroom через Google Classroom API."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="google_classroom_submit_grade",
            version="1.0.0",
            name="Google Classroom Submit Grade",
            description="Отправка оценок студентов в Google Classroom через Classroom API",
            category="education",
            icon_s3_key="icons/integrations/google-classroom.svg",
            color="#0D87E4",
            config_schema={
                "type": "object",
                "required": ["course_id", "student_id", "grade", "grade_category"],
                "properties": {
                    "course_id": {
                        "type": "string",
                        "title": "Course ID",
                        "description": "ID курса в Google Classroom"
                    },
                    "student_id": {
                        "type": "string",
                        "title": "Student ID",
                        "description": "ID студента в Google Classroom"
                    },
                    "grade": {
                        "type": "number",
                        "title": "Grade",
                        "description": "Оценка для отправки",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "grade_category": {
                        "type": "string",
                        "title": "Grade Category",
                        "description": "Категория оценки (например, 'homework', 'exam', 'project')"
                    },
                    "grade_scale": {
                        "type": "string",
                        "title": "Grade Scale",
                        "description": "Шкала оценок",
                        "enum": ["percentage", "points", "letter"],
                        "default": "percentage"
                    },
                    "max_points": {
                        "type": "number",
                        "title": "Max Points",
                        "description": "Максимальный балл (для шкалы 'points')",
                        "default": 100
                    },
                    "assignment_title": {
                        "type": "string",
                        "title": "Assignment Title",
                        "description": "Название задания"
                    },
                    "assignment_description": {
                        "type": "string",
                        "title": "Assignment Description",
                        "description": "Описание задания"
                    }
                }
            },
            credentials_provider="google_classroom",
            credentials_strategy="oauth",
            library_name="google-api-python-client>=2.0.0" if GOOGLE_CLASSROOM_AVAILABLE else None,
            examples=[
                {
                    "title": "Отправка оценки за экзамен",
                    "config": {
                        "course_id": "1234567890",
                        "student_id": "student123",
                        "grade": 85.5,
                        "grade_category": "exam",
                        "assignment_title": "Midterm Exam"
                    }
                },
                {
                    "title": "Отправка оценки за домашнее задание",
                    "config": {
                        "course_id": "1234567890",
                        "student_id": "student456",
                        "grade": 92,
                        "grade_category": "homework",
                        "assignment_title": "Week 3 Assignment"
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

        # Получаем параметры из config
        course_id = config.get("course_id")
        student_id = config.get("student_id")
        grade = config.get("grade")
        grade_category = config.get("grade_category")
        grade_scale = config.get("grade_scale", "percentage")
        max_points = config.get("max_points", 100)
        assignment_title = config.get("assignment_title")
        assignment_description = config.get("assignment_description")

        if not course_id or not student_id or grade is None or not grade_category:
            await logger.error("course_id, student_id, grade and grade_category are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "course_id, student_id, grade and grade_category are required"
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
                        "https://www.googleapis.com/auth/classroom.profile.photos",
                        "https://www.googleapis.com/auth/classroom.student-submissions.students-migrate"]
            )

            # Создаем сервис для работы с Google Classroom
            service = build('classroom', 'v1', credentials=credentials)

            # Сначала проверим, существует ли курс
            try:
                course = service.courses().get(id=course_id).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Course with ID {course_id} not found"
                        }
                    }
                else:
                    raise e

            # Найдем задание (course work) в классе, соответствующее категории
            # В Google Classroom для отправки оценки нужно сначала создать задание
            course_work_body = {
                'title': assignment_title or f'Assignment - {grade_category}',
                'description': assignment_description or f'Assignment for {grade_category} category',
                'state': 'PUBLISHED',
                'dueDate': {
                    'year': 2024,
                    'month': 12,
                    'day': 31
                },
                'maxPoints': max_points
            }

            # Создаем задание
            course_work = service.courses().courseWork().create(
                courseId=course_id,
                body=course_work_body
            ).execute()

            # Найдем submission для студента
            submissions = service.courses().courseWork().studentSubmissions().list(
                courseId=course_id,
                courseWorkId=course_work['id'],
                userId=student_id
            ).execute()

            if not submissions.get('studentSubmissions'):
                # Если submission не найдена, возвращаем ошибку
                return {
                    "response": {
                        "ok": False,
                        "error_code": 404,
                        "description": f"No submission found for student {student_id} in course {course_id}"
                    }
                }

            submission = submissions['studentSubmissions'][0]

            # Подготовим обновление оценки
            grade_update = {
                'draftGrade': grade,
                'assignedGrade': grade
            }

            # Обновляем submission с оценкой
            updated_submission = service.courses().courseWork().studentSubmissions().patch(
                courseId=course_id,
                courseWorkId=course_work['id'],
                id=submission['id'],
                updateMask='assignedGrade,draftGrade',
                body=grade_update
            ).execute()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": {
                        "course_id": course_id,
                        "student_id": student_id,
                        "assignment_id": course_work['id'],
                        "submission_id": updated_submission['id'],
                        "grade": updated_submission.get('assignedGrade'),
                        "max_points": max_points,
                        "grade_scale": grade_scale,
                        "grade_category": grade_category,
                        "assignment_title": course_work['title'],
                        "status": updated_submission.get('state'),
                        "creation_time": updated_submission.get('creationTime'),
                        "update_time": updated_submission.get('updateTime')
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

