"""Google интеграции."""
from .classroom_get_courses import GoogleClassroomGetCoursesIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(GoogleClassroomGetCoursesIntegration())
