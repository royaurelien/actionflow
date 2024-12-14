from abc import abstractmethod

from pydantic import BaseModel

from kinetik.common import SharedResources, StateModel
from kinetik.exceptions import ActionNotFound
from kinetik.logger import _logger
from kinetik.tools import update


class BaseAction:
    _subclasses: dict = {}
    context: BaseModel = None
    name: str

    @classmethod
    def list(cls):
        """List subclasses"""
        return sorted(list(cls._subclasses.keys()))

    @classmethod
    def by_name(cls, name, **kwargs):
        """Get subclass by name"""
        try:
            print(f"by_name: {kwargs}")
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


class Action(StateModel, BaseAction, kw_only=True):
    _id: str
    name: str = None
    description: str
    wait: bool = True
    retry: int = 1
    skip: bool = False
    continue_on_error: bool = False

    shared_resources: SharedResources = SharedResources()

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

    def execute(self):
        """Unified execution pipeline."""
        try:
            self.machine.start()
            self.machine.complete() if self.run() else self.machine.fail()
        except Exception:
            self.machine.fail()
            # raise
