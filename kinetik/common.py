import threading
from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional

import msgspec
from statemachine import Event, State, StateMachine
from statemachine.transition_list import TransitionList


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


class Machine(StateMachine):
    pending: State = State("pending", initial=True)
    running: State = State("running")
    success: State = State("success", final=True)
    failure: State = State("failure", final=True)

    cycle: TransitionList = pending.to(running) | running.to(success)
    fault: TransitionList = pending.to(failure) | running.to(failure)

    start: Event = pending.to(running)
    complete: Event = running.to(success)
    fail: Event = failure.from_(pending) | failure.from_(running)

    def on_enter_state(self, event, state):
        print(f"Entering '{state.id}' state from '{event}' event.")


class StateModel(msgspec.Struct, kw_only=True):
    create_ts: datetime = datetime.now()
    update_ts: Optional[datetime] = None

    machine: Machine = None

    def __post_init__(self):
        self.machine = Machine()
        print(id(self.machine))

    @abstractmethod
    def execute(self):
        """Method to be implemented by subclasses"""
