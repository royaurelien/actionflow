import threading
from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from transitions import Machine


class SharedResources:
    """
    Shared resource pool for actions,
    using a threading lock to ensure thread-safety
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


# class StateMachine:
#     states: List[str] = ["pending", "running", "success", "failure"]

#     def __init__(self):
#         self.machine = Machine(
#             model=self,
#             states=StateMachine.states,
#             initial="pending",
#             # ignore_invalid_triggers=True,
#         )
#         self.machine.add_transition("start", "pending", "running")
#         self.machine.add_transition("complete", "running", "success")
#         self.machine.add_transition("fail", "running", "failure")


class StateModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    state: str = Field(default="pending", exclude=True)
    # states: List[str] = ["pending", "running", "success", "failure"]
    machine: Machine = Field(default=None, exclude=True)
    create_ts: datetime = datetime.now()
    update_ts: Optional[datetime] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.machine = Machine(
            states=["pending", "running", "success", "failure"],
            initial="pending",
            # ignore_invalid_triggers=True,
        )
        self.machine.add_transition("start", "pending", "running")
        self.machine.add_transition("complete", "running", "success")
        self.machine.add_transition("fail", "running", "failure")

    @abstractmethod
    def execute(self):
        """Method to be implemented by subclasses"""
