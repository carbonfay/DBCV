import sys

from app.config import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(name)s] %(levelname)s %(message)s",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(asctime)s :: %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": True,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "default",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
    },
    "root": {
        "level": "DEBUG" if settings.LOG_LEVEL == "DEBUG" else "INFO",
        "handlers": ["console"],
    },

}
