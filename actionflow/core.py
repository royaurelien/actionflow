import importlib
import logging
import pkgutil
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, List, Tuple

import yaml

from actionflow.action import Action
from actionflow.common import StateModel
from actionflow.context import Context, Workspace
from actionflow.jobs import Job
from actionflow.tools import parse_yaml


class Flow(StateModel):
    name: str
    jobs: List[Job]
    env: dict = {}
    context: Context

    _child: str = "jobs"

    @property
    def workspace(self) -> str:
        return self.context.workspace.path

    @staticmethod
    def get_available_actions() -> List[str]:
        return sorted(Action.list())

    def init_workspace(self):
        Path(self.workspace).mkdir(parents=True, exist_ok=True)

    def next_job(self) -> Generator[Tuple[int, Job], None, None]:
        for index, job in enumerate(self.jobs, start=1):
            yield index, job

    def execute(self) -> None:
        """
        Executes the flow by starting the machine, executing each job, and handling success or failure.

        The method performs the following steps:
        1. Starts the machine.
        2. Prints a message indicating the start of execution.
        3. Iterates over the jobs and executes each one.
        4. Checks the state of each job's machine. If any job fails (state is not "success"), raises an exception.
        5. If all jobs succeed, completes the machine.

        If an exception occurs during execution:
        - Fails the machine.
        - Prints an error message with the exception details.

        Raises:
            Exception: If any job fails during execution.
        """

        self._start = datetime.now()
        logging.info(
            f"[Flow] Executing flow: {self.name}, {self._start:%Y-%m-%d %H:%M:%S}"
        )

        # self.init_workspace()

        logging.info("*" * 50)
        try:
            logging.info(f"[Flow] Starting execution... ({self.count} jobs)")
            self.machine.start()

            for index, job in self.next_job():
                job.execute(index, total=self.count)
                if job.machine.state != "success":
                    logging.error(f"Job {index}/{self.count} {job.name} failed.")
                    return

        except Exception as error:
            logging.error(f"[Flow] Failed with error: {error}")
            self.machine.fail()
            return

        self._end = datetime.now()
        logging.info(f"[Flow] Execution completed: {self._end:%Y-%m-%d %H:%M:%S}")
        self.machine.complete()

    def summary(self) -> Generator[str, None, None]:
        for job_index, job in self.next_job():
            yield f"Job {job_index}: {job.name}"
            for group_index, group in job.next_group():
                # yield f"Group {group_index}"
                for action_index, action in group.next_action():
                    yield f"Action {action_index}: {action.name} -> {action._exec_time:.5f} ({action.machine.state})"

        yield f"Total execution time: {self._exec_time}"

    @staticmethod
    def load(raw: str, obj: "Context") -> dict:
        """
        Load flow data from a YAML string.

        This function takes a YAML string as input, parses it, and returns a dictionary
        containing the flow data. It processes the environment variables and jobs defined
        in the YAML string and structures them into a new dictionary format.

        Args:
            raw (str): A string containing the YAML data.

        Returns:
            dict: A dictionary containing the parsed flow data with keys 'name', 'jobs', 'env', and 'context'.
        """

        data = yaml.safe_load(raw)
        env = data.get("env", {})
        parsed_data = parse_yaml(raw, env)

        jobs = [
            {
                "name": k,
                "steps": v["steps"],
            }
            for k, v in parsed_data["jobs"].items()
        ]

        context_vals = data.get("context", {})
        context_vals["workspace"] = Workspace(path=context_vals.pop("workspace"))
        # print(context_vals)
        # print(obj)
        # context = obj(**context_vals)
        # print(context)

        return {
            "name": parsed_data["name"],
            "jobs": jobs,
            "env": env,
            "context": context_vals,
        }

    @classmethod
    def from_file(cls, filepath: str) -> "Flow":
        """
        Create a Flow instance from a file.

        Args:
            filepath (str): The path to the file containing the flow data.

        Returns:
            Flow: An instance of the Flow class created from the file data.

        Raises:
            FileNotFoundError: If the file at the specified path does not exist.
            IOError: If there is an error reading the file.
            ValidationError: If the data in the file is not valid for creating a Flow instance.
        """

        obj = cls.model_fields["context"].annotation

        with open(filepath, "r") as file:
            raw = file.read()
            data = cls.load(raw, obj)

        return cls.model_validate(data)

    @classmethod
    def from_string(cls, raw: str) -> "Flow":
        """
        Create a Flow instance from a raw string.

        Args:
            raw (str): The raw string to be parsed and converted into a Flow instance.

        Returns:
            Flow: An instance of the Flow class created from the parsed data.
        """

        obj = cls.model_fields["context"].annotation
        data = cls.load(raw, obj)
        return cls.model_validate(data)

    @staticmethod
    def load_all_actions(*args) -> None:
        names = list(map(str, args))

        if not names or "actionflow.actions" not in names:
            names.insert(0, "actionflow.actions")

        logging.debug(f"Loading actions from: {', '.join(names)}")

        for package_name in names:
            package = importlib.import_module(package_name)
            for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
                if not is_pkg:
                    importlib.import_module(f"{package_name}.{module_name}")

        logging.info(
            f"Loaded actions ({len(Action.list())}): {', '.join(Action.list())}"
        )

    def model_post_init(self, __context: Any) -> None:
        # Add context to steps
        for job in self.jobs:
            for step in job.steps:
                step._context = self.context
        super().model_post_init(__context)


if __name__ == "__main__":
    raw = """
name: example
context:
  mode: test
  workspace: /tmp
  test: true
env:
  key1: value1
  key2: value2
jobs:
  job1:
    steps:
      - name: example
        with:
          concurrency: false
      - name: fail
        with:
          concurrency: false
      - name: example
        with:
          concurrency: true
  job2:
    steps:
      - name: example
        with:
          concurrency: true
      - name: example
        with:
          concurrency: true
"""

    Flow.load_all_actions()

    flow = Flow.from_string(raw)
    flow.execute()
