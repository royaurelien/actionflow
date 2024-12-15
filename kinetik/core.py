import importlib
import pkgutil
from datetime import datetime
from typing import Generator, List, Tuple

import yaml

from kinetik.action import Action
from kinetik.common import StateModel
from kinetik.context import Context
from kinetik.jobs import Job
from kinetik.logger import _logger
from kinetik.tools import load_yaml_with_context


class Flow(StateModel):
    name: str
    jobs: List[Job]
    env: dict = {}
    context: dict = {}
    workspace: str

    _start: datetime = None
    _end: datetime = None

    @property
    def jobs_count(self):
        return len(self.jobs)

    def next_job(self) -> Generator[Tuple[int, Job], None, None]:
        for index, job in enumerate(self.jobs, start=1):
            yield index, job

    def execute(self):
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

        try:
            _logger.info(f"[Flow] Starting execution... ({self.jobs_count} jobs)")
            self.machine.start()

            for index, job in self.next_job():
                job.execute()
                if job.machine.state != "success":
                    _logger.error(f"Job {index}/{self.jobs_count} {job.name} failed.")
                    return

        except Exception as error:
            _logger.error(f"[Flow] Failed with error: {error}")
            self.machine.fail()
            return

        self.machine.complete()

    def summary(self):
        for job_index, job in self.next_job():
            for group_index, group in job.next_group():
                for action_index, action in group.next_action():
                    print(action.summary())

    @staticmethod
    def load(raw: str) -> dict:
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
        parsed_data = load_yaml_with_context(raw, env)

        jobs = [
            {
                "name": k,
                "steps": v["steps"],
            }
            for k, v in parsed_data["jobs"].items()
        ]

        context = Context()
        context.initialize(parsed_data.get("context", {}))

        return {
            "name": parsed_data["name"],
            "jobs": jobs,
            "env": env,
            "workspace": parsed_data.get("context", {}).get("workspace", ""),
            "context": parsed_data.get("context", {}),
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
        with open(filepath, "r") as file:
            raw = file.read()
            data = cls.load(raw)

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
        data = cls.load(raw)
        return cls.model_validate(data)

    @staticmethod
    def load_all_actions():
        package_name = "kinetik.actions"
        package = importlib.import_module(package_name)
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if not is_pkg:
                importlib.import_module(f"{package_name}.{module_name}")


if __name__ == "__main__":
    raw = """
name: example
context:
  mode: test
env:
  key1: value1
  key2: value2
jobs:
  job1:
    steps:
      - name: example
        with:
          wait: false
      - name: fail
        with:
          wait: false
      - name: example
        with:
          wait: true
  job2:
    steps:
      - name: example
        with:
          wait: true
      - name: example
        with:
          wait: true
"""
    from kinetik import load_all_actions

    load_all_actions()
    print(Action.list())

    flow = Flow.from_string(raw)
    flow.execute()
