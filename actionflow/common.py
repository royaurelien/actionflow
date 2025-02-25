import logging
import threading
import time
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, computed_field
from transitions import Machine

logging.getLogger("transitions").setLevel(logging.WARNING)


class SharedResources:
    """
    A thread-safe class for managing shared resources.

    Attributes:
        lock (threading.Lock): A lock to ensure thread-safe access to resources.
        resources (dict): A dictionary to store shared resources.

    Methods:
        get_resource(resource_name: str):
            Retrieves the resource associated with the given name.
            Args:
                resource_name (str): The name of the resource to retrieve.
            Returns:
                The resource associated with the given name, or None if not found.

        set_resource(resource_name: str, value: Any):
            Sets the resource associated with the given name to the specified value.
            Args:
                resource_name (str): The name of the resource to set.
                value (Any): The value to associate with the resource name.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.resources: dict = {}

    def get_resource(self, resource_name: str):
        with self.lock:
            return self.resources.get(resource_name)

    def set_resource(self, resource_name: str, value: Any):
        with self.lock:
            self.resources[resource_name] = value


class ExecutionModel(object):
    _create_ts: datetime = datetime.now()
    _start_ts: Optional[datetime] = None
    _end_ts: Optional[datetime] = None
    _start: Optional[float] = None
    _end: Optional[float] = None
    _short: bool = False
    _child: str = None

    def start_counter(self) -> None:
        if not self._short:
            self._start_ts = datetime.now()
        else:
            self._start = time.perf_counter()

    def stop_counter(self) -> None:
        if not self._short:
            self._end_ts = datetime.now()
        else:
            self._end = time.perf_counter()

    @property
    def _exec_time(self) -> Union[timedelta, float]:
        return self._end - self._start if self._short else self._end_ts - self._start_ts


class StateModel(BaseModel):
    """
    StateModel is a class that represents the state of a machine with transitions between different states.

    Attributes:
        model_config (ConfigDict): Configuration for the model allowing arbitrary types.
        state (str): The current state of the machine, default is "pending".
        machine (Machine): The state machine instance.
        create_ts (datetime): Timestamp when the state model was created.
        update_ts (Optional[datetime]): Timestamp when the state model was last updated.

    Methods:
        __init__(**kwargs): Initializes the StateModel instance and sets up the state machine with transitions.
        execute(): Abstract method to be implemented by subclasses to define specific execution logic.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    state: str = Field(default="pending", exclude=True)
    machine: Machine = Field(default=None, exclude=True)
    _create_ts: datetime = datetime.now()
    _start_ts: Optional[datetime] = None
    _end_ts: Optional[datetime] = None
    _start: Optional[float] = 0.0
    _end: Optional[float] = 0.0
    _short: bool = False

    @property
    def _name(self) -> str:
        name = getattr(self, "name", None)
        return f"{self.__class__.__name__}: {name}" if name else self.__class__.__name__

    def on_enter_running(self) -> None:
        logging.info(f"[{self._name}] Started execution")
        if not self._short:
            self._start_ts = datetime.now()
        else:
            self._start = time.perf_counter()

    def on_exit_running(self) -> None:
        if not self._short:
            self._end_ts = datetime.now()
        else:
            self._end = time.perf_counter()

    def on_enter_success(self) -> None:
        logging.info(f"[{self._name}] Completed execution in {self._exec_time}")

    @property
    def _exec_time(self) -> Union[timedelta, float]:
        return (
            (self._end - self._start) or timedelta(seconds=0)
            if self._short
            else (self._end_ts - self._start_ts)
            if self._end_ts and self._start_ts
            else 0.0
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.machine = Machine(
            states=["pending", "running", "success", "failure"],
            initial="pending",
        )
        self.machine.add_transition("start", "pending", "running")
        self.machine.add_transition("complete", "running", "success")
        self.machine.add_transition("fail", "running", "failure")
        self.machine.on_enter_running(lambda: self.on_enter_running())
        self.machine.on_exit_running(lambda: self.on_exit_running())
        self.machine.on_enter_success(lambda: self.on_enter_success())

    @abstractmethod
    def execute(self, index: int, total: int) -> None:
        """Method to be implemented by subclasses"""

    @computed_field
    def count(self) -> int:
        return len(getattr(self, "_child", 0))
