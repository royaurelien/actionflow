from concurrent.futures import ThreadPoolExecutor
from typing import List

from pydantic import model_validator

from kinetik.actions.base import Action
from kinetik.common import StateModel
from kinetik.exceptions import ActionNotFound
from kinetik.logger import _logger
from kinetik.tools import group_by


class Group(StateModel):
    actions: List[Action]

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

    def execute(self):
        try:
            self.machine.start()
            _logger.info(f"[Job: {self.name}] Starting execution...")

            total = len(self.grouped)
            for index, actions in enumerate(self.grouped, start=1):
                _logger.info(
                    f"[Group {index}/{total}] Executing actions in parallel..."
                )
                group = Group(actions=actions)
                group.execute()
                if group.machine.state != "success":
                    self.machine.fail()
                    # raise Exception("Group execution failed.")
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
