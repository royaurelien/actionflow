from typing import List

import yaml
from pydantic import BaseModel

from kinetik.actions.base import Action
from kinetik.common import StateModel
from kinetik.jobs import Job


class FlowSchema(BaseModel):
    name: str
    env: dict = {}


class Flow(StateModel):
    jobs: List[Job]

    def execute(self):
        try:
            self.start()
            print("[Flow] Starting execution...")
            for job in self.jobs:
                job.execute()
                if job.state != "success":
                    raise Exception(f"Job {job.name} failed.")
            self.complete()
        except Exception as e:
            self.fail()
            print(f"[Flow] Failed with error: {e}")

    @classmethod
    def from_file(cls, filepath: str) -> "Flow":
        with open(filepath, "r") as file:
            config = yaml.safe_load(file)

        return cls.model_validate(config)

    @classmethod
    def from_string(cls, raw: str) -> "Flow":
        config = yaml.safe_load(raw)

        print(config)

        return cls.model_validate(config)


if __name__ == "__main__":
    data = """
jobs:
  - name: job1
    steps:
      - name: example
        wait: true
  #     - name: example
  #       wait: false
  #     - name: example
  #       wait: true
  # - name: job2
  #   steps:
  #     - name: example
  #       wait: false
  #     - name: example
  #       wait: true
"""
    from kinetik import load_all_actions

    load_all_actions()
    print(Action.list())
    flow = Flow.from_string(data)
    flow.execute()
