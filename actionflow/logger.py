import logging
import time
from functools import wraps

# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer
from actionflow.settings import settings


def configure_logger(logfile: str = settings.logfile, debug: bool = settings.debug):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s"
    )
    # "format": "%(asctime)s | %(levelname)s | %(message)s",

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def logs(function):
    """Logs decorator to benchmark method execution"""

    @wraps(function)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        logging.debug("%s: start", function.__qualname__)
        output = function(*args, **kwargs)

        end = time.perf_counter()
        message = f"{function.__qualname__}: end ({end - start:.6f})"  # noqa: E231
        logging.debug(message)

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

            try:
                setattr(obj, attrs[-1], end - start)
            except AttributeError as error:
                logging.error(f"Error setting attribute: {error}")

            return output

        return wrapper

    return decorator_repeat


# class LogFileHandler(FileSystemEventHandler):
#     """
#     Custom handler to process file modifications.
#     """

#     def __init__(self, file_path):
#         self.file_path = file_path

#     def on_modified(self, event):
#         if event.src_path == self.file_path:
#             with open(self.file_path, "r") as file:
#                 # Print only the new lines
#                 print(file.readlines()[-1], end="")


# def getLogfileObserver():
#     """Get observer for log file"""

#     observer = Observer()
#     observer.schedule(
#         LogFileHandler(os.path.join(settings.workdir, settings.logfile)),
#         os.path.join(settings.workdir, settings.logfile),
#     )
#     return observer
