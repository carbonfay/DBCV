"""Google интеграции."""
from .classroom_create_course import GoogleClassroomCreateCourseIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GoogleClassroomCreateCourseIntegration())
