import time

from actionflow.action import Action


class ExampleAction(Action):
    name: str = "example"
    description: str = "An example action"
    kind: str = None

    def _run(self) -> bool:
        time.sleep(5)
        return True


class FailAction(Action):
    name: str = "fail"
    description: str = "An example action"
    retry: int = 3

    def _run(self) -> bool:
        return not bool(self.retry - 1)


if __name__ == "__main__":
    print(Action.list())

    example = ExampleAction(kind="test")
    # print(example.machine.start())
    print(example.machine.state)

    example.execute()
    print(example.machine.state)
