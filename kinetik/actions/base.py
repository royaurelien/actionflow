import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from kinetik.exceptions import ActionNotFound
from kinetik.logger import _logger
from kinetik.tools import update


# Shared resource pool using a threading lock to ensure thread-safety
class SharedResources:
    def __init__(self):
        self.lock = threading.Lock()
        self.resources: dict = {}

    def get_resource(self, resource_name: str):
        with self.lock:
            return self.resources.get(resource_name)

    def set_resource(self, resource_name: str, value: Any):
        with self.lock:
            self.resources[resource_name] = value


class BaseAction(ABC):
    name: str
    context: BaseModel = None
    _subclasses: dict = {}

    @classmethod
    def list(cls):
        """List subclasses"""
        return sorted(list(cls._subclasses.keys()))

    @classmethod
    def by_name(cls, name, **kwargs):
        """Get subclass by name"""
        try:
            return cls._subclasses[name](**kwargs)
        except KeyError:
            raise ActionNotFound(f"'{name}' not found")

    def set_context(self, context: BaseModel):
        """Set context for the action"""
        self.context = context

    @abstractmethod
    def _run(self):
        """Method to be implemented by subclasses"""

    def _check(self) -> bool:
        """Method to be implemented by subclasses"""
        return True

    def _pre_process(self):
        """Method to be implemented by subclasses"""

    def _post_process(self):
        """Method to be implemented by subclasses"""

    def __init_subclass__(cls):
        if cls.name is not None:
            BaseAction._subclasses[cls.name] = cls


class Action(BaseAction, BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _id: str
    name: str = None
    description: str
    wait: bool = True
    retry: int = 1
    skip: bool = False
    continue_on_error: bool = False
    state: str = "pending"
    create_ts: datetime = datetime.now()
    update_ts: Optional[datetime] = None
    shared_resources: SharedResources = SharedResources()  # Shared resource pool

    @update("update_ts")
    def run(self, ctx: BaseModel = None) -> bool:
        """Run the action with retry logic"""
        try:
            while self.retry > 0:
                # Check if the action should be skipped
                if self.skip and self._check():
                    _logger.info(f"{self.name} already satisfied, skipping.")
                    return True

                self._pre_process()

                if self._run():  # If the action succeeds, stop retrying
                    _logger.info(f"{self.name} completed successfully.")
                    self._post_process()
                    return self._check()
                if self.continue_on_error:
                    _logger.warning("Error occurred, continuing despite failure.")
                    return True
                self.retry -= 1
                _logger.info(f"Retrying {self.name}, attempts left: {self.retry}")
        except Exception as error:
            _logger.error(f"Error running action {self.name}: {error}")
            raise

        return False
