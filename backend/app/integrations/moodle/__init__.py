"""Moodle интеграции."""
from .get_course import MoodleGetCourseIntegration
from app.integrations.registry import registry

# Регистрация интеграции
registry.register(MoodleGetCourseIntegration())

