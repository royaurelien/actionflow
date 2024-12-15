import logging
import os
import time
from functools import wraps
from logging.config import dictConfig

from pydantic import BaseModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from actionflow.settings import settings

__all__ = ["logger", "_logger", "logs"]


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "upgradekit"
    LOG_FORMAT: str = "%(asctime)s | %(levelprefix)s | %(message)s"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(message)s",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": os.path.join(settings.workdir, settings.logfile),
        },
    }
    loggers: dict = {
        LOGGER_NAME: {"handlers": ["default", "file"], "level": LOG_LEVEL},
    }


dictConfig(LogConfig().model_dump())

_logger = logger = logging.getLogger("upgradekit")


def logs(function):
    """Logs decorator to benchmark method execution"""

    @wraps(function)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        logger.debug("%s: start", function.__qualname__)
        output = function(*args, **kwargs)

        end = time.perf_counter()
        message = f"{function.__qualname__}: end ({end - start:.6f})"  # noqa: E231
        logger.debug(message)

        return output

    return wrapper


def log_execution(fieldnames: str):
    def decorator_repeat(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            output = func(*args, **kwargs)
            end = time.perf_counter()

            self = args[0]

            obj = self
            attrs = fieldnames.split(".")
            for attr in attrs[:-1]:
                obj = getattr(obj, attr)
            setattr(obj, attrs[-1], end - start)

            return output

        return wrapper

    return decorator_repeat


class LogFileHandler(FileSystemEventHandler):
    """
    Custom handler to process file modifications.
    """

    def __init__(self, file_path):
        self.file_path = file_path

    def on_modified(self, event):
        if event.src_path == self.file_path:
            with open(self.file_path, "r") as file:
                # Print only the new lines
                print(file.readlines()[-1], end="")


def getLogfileObserver():
    """Get observer for log file"""

    observer = Observer()
    observer.schedule(
        LogFileHandler(os.path.join(settings.workdir, settings.logfile)),
        os.path.join(settings.workdir, settings.logfile),
    )
    return observer
