import threading
from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from transitions import Machine


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

    model_config = ConfigDict(arbitrary_types_allowed=True)
    state: str = Field(default="pending", exclude=True)
    machine: Machine = Field(default=None, exclude=True)
    create_ts: datetime = datetime.now()
    update_ts: Optional[datetime] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.machine = Machine(
            states=["pending", "running", "success", "failure"],
            initial="pending",
        )
        self.machine.add_transition("start", "pending", "running")
        self.machine.add_transition("complete", "running", "success")
        self.machine.add_transition("fail", "running", "failure")

    @abstractmethod
    def execute(self):
        """Method to be implemented by subclasses"""
