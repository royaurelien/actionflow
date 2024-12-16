from concurrent.futures import ThreadPoolExecutor
from typing import Generator, List, Tuple

from pydantic import model_validator

from actionflow.action import Action
from actionflow.common import StateModel
from actionflow.exceptions import ActionNotFound
from actionflow.logger import _logger
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

    def next_action(self) -> Generator[Tuple[int, Action], None, None]:
        for index, action in enumerate(self.actions, start=1):
            yield index, action

    def execute(self):
        try:
            # _logger.info("[Group] Executing actions in parallel...")
            self.machine.start()

            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(action.execute) for action in self.actions]
                for future in futures:
                    # Wait for all actions to complete
                    future.result()

            if not all(action.machine.state == "success" for action in self.actions):
                self.machine.fail()
                return

        except Exception as e:
            self.machine.fail()
            _logger.info(f"[Group] Failed with error: {e}")
            return

        # _logger.info("[Group] All actions completed successfully.")
        self.machine.complete()


class Job(StateModel):
    """
    Represents a job consisting of a series of actions to be executed.

    Attributes:
        name (str): The name of the job.
        steps (List[Action]): A list of actions to be executed as part of the job.

    Methods:
        preprocess_data(cls, values):
            Replaces steps with action instances created from the registry.

        length() -> int:
            Returns the number of steps in the job.

        grouped() -> List[List[Action]]:
            Groups the steps by the "wait" attribute.

        set_indexes(index: int) -> None:
            Sets unique indexes for each action in the job.

        next_group() -> Generator[Tuple[int, Group], None, None]:
            Yields the next group of actions to be executed.

        execute():
            Executes the job by running all actions in sequence, handling state transitions and logging.
    """

    name: str
    steps: List[Action]

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
                _logger.error(f"Action not found: {name}")
                exit(1)
            steps.append(action)

        values["steps"] = steps
        return values

    @property
    def length(self) -> int:
        return len(self.steps)

    @property
    def grouped(self) -> List[List[Action]]:
        return group_by(self.steps, "wait")

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

    def execute(self):
        try:
            self.machine.start()
            _logger.info(f"[Job: {self.name}] Starting execution...")

            total = len(self.grouped)
            for index, group in self.next_group():
                _logger.info(
                    f"[Group {index}/{total}] Executing actions in parallel..."
                )

                group.execute()
                if group.machine.state != "success":
                    self.machine.fail()
                    return

                _logger.info(
                    f"[Group {index}/{total}] All actions completed successfully."
                )

            _logger.info(f"[Job: {self.name}] Completed successfully.")

        except Exception as e:
            _logger.info(f"[Job: {self.name}] Failed with error: {e}")
            self.machine.fail()
            return

        self.machine.complete()
