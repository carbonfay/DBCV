from app.integrations.registry import registry
from .get_courses import MoodleGetCoursesIntegration

registry.register(MoodleGetCoursesIntegration())
