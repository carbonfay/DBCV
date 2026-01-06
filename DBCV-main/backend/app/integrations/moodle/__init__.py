# Если файл назывался get_courses, удали старый импорт
from .create_course import MoodleCreateCourseIntegration
from app.integrations.registry import registry

registry.register(MoodleCreateCourseIntegration())