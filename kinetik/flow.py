from typing import List

import yaml
from pydantic import BaseModel

from kinetik.actions.base import Action
from kinetik.common import StateModel
from kinetik.core import Context
from kinetik.jobs import Job
from kinetik.logger import _logger
from kinetik.tools import load_yaml_with_context


class FlowSchema(BaseModel):
    name: str
    env: dict = {}


class Flow(StateModel):
    name: str
    jobs: List[Job]
    env: dict = {}
    context: dict = {}
    workspace: str

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
        total = len(self.jobs)
        try:
            _logger.info(f"[Flow] Starting execution... ({total} jobs)")
            self.machine.start()

            for index, job in enumerate(self.jobs, start=1):
                job.execute()
                if job.machine.state != "success":
                    _logger.error(f"Job {index}/{total} {job.name} failed.")
                    return

        except Exception as error:
            _logger.error(f"[Flow] Failed with error: {error}")
            self.machine.fail()
            return

        self.machine.complete()

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

    # data = yaml.safe_load(raw)
    # print(data)

    flow = Flow.from_string(raw)
    flow.execute()

    print(flow.context)

    # {
    #     "jobs": {
    #         "job1": {"steps": {"example": {"with": {"wait": True}}}},
    #         "job2": {"steps": {"example": {"with": {"wait": True}}}},
    #     }
    # }

    # {
    #     "jobs": [
    #         {"name": "job1", "steps": [{"name": "example", "with": {"wait": True}}]},
    #         {"name": "job2", "steps": [{"name": "example", "with": {"wait": True}}]},
    #     ]
    # }
