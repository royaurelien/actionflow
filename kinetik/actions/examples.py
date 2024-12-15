from kinetik.actions.base import Action


class ExampleAction(Action):
    name: str = "example"
    description: str = "An example action"
    kind: str = None

    def _run(self) -> bool:
        print(f"[{self.name}] Running action")
        return True


if __name__ == "__main__":
    print(Action.list())

    example = ExampleAction(kind="test")
    # print(example.machine.start())
    print(example.machine.state)

    example.execute()
    print(example.machine.state)
