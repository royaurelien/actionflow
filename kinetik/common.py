import threading
from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional

import msgspec

# from msgspec.structs import force_setattr
# from pydantic import BaseModel, ConfigDict, Field
# from transitions.core import _LOGGER
from transitions import Machine

# class NewMachine(Machine):
#     def _checked_assignment(self, model, name, func):
#         bound_func = getattr(model, name, None)
#         if (bound_func is None) ^ self.model_override:
#             # setattr(model, name, func)
#             force_setattr(model, name, func)
#         else:
#             _LOGGER.warning(
#                 "%sSkip binding of '%s' to model due to model override policy.",
#                 self.name,
#                 name,
#             )


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


class StateModel(msgspec.Struct, kw_only=True, dict=True, forbid_unknown_fields=True):
    # model_config = ConfigDict(arbitrary_types_allowed=True)
    # state: str = Field(default="pending", exclude=True)
    # states: List[str] = ["pending", "running", "success", "failure"]
    # machine: Machine = Machine(
    #     states=["pending", "running", "success", "failure"],
    #     initial="pending",
    #     transitions=[
    #         {"trigger": "start", "source": "pending", "dest": "running"},
    #         {"trigger": "complete", "source": "running", "dest": "success"},
    #         {"trigger": "fail", "source": "running", "dest": "failure"},
    #     ],
    #     # ignore_invalid_triggers=True,
    # )
    create_ts: datetime = datetime.now()
    update_ts: Optional[datetime] = None
    machine: Machine = None  # Machine is initialized dynamically

    # def __setattr__(self, name: str, value: Any):
    #     """Allow dynamic attribute setting."""
    #     super().__setattr__(name, value)
    #     # try:
    #     #     super().__setattr__(name, value)
    #     # except AttributeError:
    #     #     # If the attribute doesn't exist in the defined fields, store it dynamically
    #     #     # msgspec.structs.force_setattr(self, name, value)
    #     #     object.__setattr__(self, name, value)

    # def __getattr__(self, name: str):
    #     """Provide dynamic attribute access for machine methods."""
    #     # Use `object.__getattribute__` to avoid recursion
    #     try:
    #         return object.__getattribute__(self, name)
    #     except AttributeError:
    #         raise AttributeError(
    #             f"'{type(self).__name__}' object has no attribute '{name}'"
    #         )

    def __post_init__(self):
        self._initialize_machine()

    def _initialize_machine(self):
        """Initialize the state machine."""
        self.machine = Machine(
            model=self,
            states=["pending", "running", "success", "failure"],
            initial="pending",
        )
        self.machine.add_transition("start", "pending", "running")
        self.machine.add_transition("complete", "running", "success")
        self.machine.add_transition("fail", "running", "failure")

    # @property
    # def state(self):
    #     return self.machine.state

    # def __post_init__(self):
    #     self.machine = Machine(
    #         model=self,
    #         states=["pending", "running", "success", "failure"],
    #         initial="pending",
    #         # ignore_invalid_triggers=True,
    #     )
    #     self.machine.add_transition("start", "pending", "running")
    #     self.machine.add_transition("complete", "running", "success")
    #     self.machine.add_transition("fail", "running", "failure")

    @abstractmethod
    def execute(self):
        """Method to be implemented by subclasses"""
