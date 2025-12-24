"""Moodle интеграции."""
from .get_course import MoodleGetCourseIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(MoodleGetCourseIntegration())

