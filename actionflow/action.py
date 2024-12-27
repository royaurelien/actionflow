import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from actionflow.common import SharedResources, StateModel
from actionflow.context import Context
from actionflow.exceptions import ActionNotFound


class BaseAction(ABC):
    name: str
    _context: Context
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


class Action(BaseAction, StateModel):
    _short: bool = True
    name: str = None
    description: str
    concurrency: bool = False
    retry: int = 1
    skip: bool = False
    continue_on_error: bool = False

    shared_resources: SharedResources = SharedResources()

    def run(self) -> bool:
        """Run the action with retry logic"""
        try:
            while self.retry > 0:
                # Check if the action should be skipped
                if self.skip and self._check():
                    logging.info(f"[Action: {self.name}] already satisfied, skipping.")
                    return True

                # logging.info(f"[Action: {self.name}] executing.")
                self._pre_process()

                if self._run():  # If the action succeeds, stop retrying
                    # logging.info(f"[Action: {self.name}] completed successfully.")
                    self._post_process()
                    return self._check()
                if self.continue_on_error:
                    logging.warning(
                        f"[Action: {self.name}] Error occurred, continuing despite failure."
                    )
                    self._post_process()
                    return True
                self.retry -= 1
                logging.warning(
                    f"[Action: {self.name}] Retrying, attempts left: {self.retry}"
                )
        except Exception as error:
            logging.error(f"[Action: {self.name}] Error: {error}")
            raise

        return False

    def execute(self, index: int, total: int) -> None:
        """Unified execution pipeline."""
        self.machine.start()
        try:
            self.machine.complete() if self.run() else self.machine.fail()
        except Exception as error:
            logging.error(f"Error executing action {self.name}: {error}")
            self.machine.fail()

    def summary(self):
        """Summary of the action"""
        return {
            "name": self.name,
            "state": self.machine.state,
            "exec": self._exec_time,
        }
