"""Moodle интеграции (версия 2)."""
from .get_courses import MoodleGetCoursesIntegration
from app.integrations.registry import registry

# Автоматическая регистрация интеграций
registry.register(MoodleGetCoursesIntegration())

__all__ = ["MoodleGetCoursesIntegration"]

