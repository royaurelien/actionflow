import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from pydantic import BaseModel


class SingletonMeta(type):
    """
    Métaclasse pour implémenter un singleton thread-safe.
    """

    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        # Double vérification avec verrouillage
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


@dataclass(frozen=True)
class Workspace(metaclass=SingletonMeta):
    path: str

    def __post_init__(self):
        Path(self.path).mkdir(parents=True, exist_ok=True)
        logging.info("Workspace created")

    def get_path(self, *args) -> str:
        return str(Path(self.path).joinpath(*args))

    def make_path(self, *args) -> None:
        Path(self.path).joinpath(*args).mkdir(parents=True, exist_ok=True)


class Context(BaseModel):
    workspace: Workspace
