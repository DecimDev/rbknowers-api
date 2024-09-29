import logging
from logging.config import dictConfig

class LogConfig:
    """Logging configuration to be set for the server"""

    LOG_FORMAT = "%(levelprefix)s | %(asctime)s | %(message)s"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "app": {"handlers": ["default"], "level": "DEBUG"},
        },
    }

def setup_logging():
    dictConfig(LogConfig.logging_config)

# Call setup_logging() at the start of your application
setup_logging()