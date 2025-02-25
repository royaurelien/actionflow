import logging
import time

from actionflow.action import Action
from actionflow.context import Workspace


class ExampleAction(Action):
    name: str = "example"
    description: str = "An example action"
    kind: str = None

    def _run(self) -> bool:
        logging.info(f"Running {self.name} on {Workspace().path}")
        time.sleep(5)
        return True


class FailAction(Action):
    name: str = "fail"
    description: str = "An example action"
    retry: int = 3

    def _run(self) -> bool:
        return not bool(self.retry - 1)


class BlockingAction(Action):
    name: str = "example-blocking"
    description: str = "Blocking action"
    time: int = 5
    concurrency: bool = True

    def _run(self):
        time.sleep(self.time)
        return True


if __name__ == "__main__":
    print(Action.list())

    example = ExampleAction(kind="test")
    example.execute()
