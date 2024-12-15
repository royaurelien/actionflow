from concurrent.futures import ThreadPoolExecutor
from typing import List

from pydantic import model_validator

from kinetik.actions.base import Action
from kinetik.common import StateModel
from kinetik.tools import group_by


class Group(StateModel):
    actions: List[Action]

    def execute(self):
        try:
            self.machine.start()
            print("[Group] Executing actions in parallel...")
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(action.execute) for action in self.actions]
                for future in futures:
                    future.result()  # Wait for all actions to complete
            self.machine.complete()
        except Exception as e:
            self.machine.fail()
            print(f"[Group] Failed with error: {e}")


class Job(StateModel):
    name: str
    steps: List[Action]

    @model_validator(mode="before")
    def preprocess_data(cls, values):
        steps = []

        for step in values["steps"]:
            print(step)
            name = step.pop("name")
            action = Action.by_name(name, **step)
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
        print(self.machine.current_state)
        try:
            self.machine.start()
            print(f"[Job: {self.name}] Starting execution...")

            for actions in self.grouped:
                group = Group(actions=actions)
                group.execute()
                if group.machine.current_state != "success":
                    raise Exception("Group execution failed.")
            self.machine.complete()
        except Exception as e:
            self.machine.fail()
            print(f"[Job: {self.name}] Failed with error: {e}")
