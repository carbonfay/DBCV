from .get_courses import MoodleGetCoursesIntegration
from app.integrations.registry import registry

registry.register(MoodleGetCoursesIntegration())