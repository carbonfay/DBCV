"""Moodle интеграции."""
from .create_course import MoodleCreateCourseIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(MoodleCreateCourseIntegration())
