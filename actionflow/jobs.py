import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Generator, List, Tuple

from pydantic import model_validator

from actionflow.action import Action
from actionflow.common import StateModel
from actionflow.exceptions import ActionNotFound
from actionflow.tools import group_by


class Group(StateModel):
    """
    A class representing a group of actions to be executed in parallel.

    Attributes:
        actions (List[Action]): A list of actions to be executed.

    Methods:
        next_action() -> Generator[Tuple[int, Action], None, None]:
            Yields the index and action for each action in the group.

        execute():
            Executes all actions in the group in parallel. If any action fails,
            the group's state is set to 'fail'. If all actions succeed, the group's
            state is set to 'complete'.
    """

    actions: List[Action]
    _stop_event: threading.Event = None
    _child: str = "actions"

    def model_post_init(self, __context):
        self._stop_event = threading.Event()
        return super().model_post_init(__context)

    def next_action(self) -> Generator[Tuple[int, Action], None, None]:
        for index, action in enumerate(self.actions, start=1):
            yield index, action

    def execute(self, index: int, total: int) -> None:
        if self._stop_event.is_set():
            return

        try:
            self.machine.start()

            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(action.execute, action_index, self.count)
                    for action_index, action in enumerate(self.actions)
                ]
                for future in futures:
                    # Wait for all actions to complete
                    future.result()

            if not all(action.machine.state == "success" for action in self.actions):
                self.machine.fail()
                return

        except Exception as e:
            self.machine.fail()
            self._stop_event.set()
            logging.info(f"[Group] Failed with error: {e}")
            return

        self.machine.complete()


class Job(StateModel):
    name: str
    steps: List[Action]
    _child: str = "steps"

    @model_validator(mode="before")
    def preprocess_data(cls, values):
        """
        Replace steps with action instances created from the registry
        """
        steps = []

        for step in values["steps"]:
            name = step.pop("name")
            params = step.pop("with", {})
            try:
                action = Action.by_name(name, **params)
            except ActionNotFound:
                logging.error(f"Action not found: {name}")
                exit(1)
            steps.append(action)

        values["steps"] = steps
        return values

    @property
    def grouped(self) -> List[List[Action]]:
        return group_by(self.steps, "concurrency")

    def set_indexes(self, index: int) -> None:
        for group_index, group in enumerate(self.grouped, start=1):
            for action_index, action in enumerate(group, start=1):
                action._id = (
                    f"{index}_{self.name}_{group_index}_{action_index}_{action.name}"
                )

    def next_group(self) -> Generator[Tuple[int, Group], None, None]:
        for index, actions in enumerate(self.grouped, start=1):
            group = Group(actions=actions)
            yield index, group

    def execute(self, index: int, total: int) -> None:
        try:
            self.machine.start()
            # logging.info(f"[Job: {self.name}] Starting execution...")

            # total = len(self.grouped)
            for group_index, group in self.next_group():
                # logging.info(
                #     f"[Group {index}/{total}] Executing actions in parallel..."
                # )

                group.execute(group_index, self.count)
                if group.machine.state != "success":
                    self.machine.fail()
                    return

                # logging.info(
                # f"[Group {index}/{total}] All actions completed successfully."
                # )

            # logging.info(f"[Job: {self.name}] Completed successfully.")

        except Exception as e:
            logging.info(f"[Job: {self.name}] Failed with error: {e}")
            self.machine.fail()
            return

        self.machine.complete()
