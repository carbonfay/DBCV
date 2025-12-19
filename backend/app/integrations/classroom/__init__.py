"""Classroom интеграции."""
from .submit_grade import GoogleClassroomSubmitGradeIntegration
from .create_course import GoogleClassroomCreateCourseIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GoogleClassroomSubmitGradeIntegration())
registry.register(GoogleClassroomCreateCourseIntegration())
