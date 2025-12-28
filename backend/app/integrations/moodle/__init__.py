from app.integrations.registry import registry
from .get_courses import MoodleGetCoursesIntegration
from .get_course import MoodleGetCourseIntegration

registry.register(MoodleGetCoursesIntegration())
registry.register(MoodleGetCourseIntegration())
