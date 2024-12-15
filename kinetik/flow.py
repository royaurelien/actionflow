# from dataclasses import dataclass
from typing import List

import yaml
from pydantic import BaseModel

from kinetik.actions.base import Action
from kinetik.common import StateModel
from kinetik.jobs import Job
from kinetik.logger import _logger
from kinetik.settings import settings


class FlowSchema(BaseModel):
    name: str
    env: dict = {}


class Flow(StateModel):
    jobs: List[Job]

    def execute(self):
        try:
            self.machine.start()
            print("[Flow] Starting execution...")
            for job in self.jobs:
                job.execute()
                if job.machine.current_state != "success":
                    raise Exception(f"Job {job.name} failed.")
            self.machine.complete()
        except Exception as e:
            self.machine.fail()

            print(f"[Flow] Failed with error: {e}")

    def __post_init__(self):
        super().__post_init__()
        for index, job in enumerate(self.jobs, start=1):
            job.set_indexes(index)

    @classmethod
    def from_file(cls, filepath: str) -> "Flow":
        with open(filepath, "r") as file:
            config = yaml.safe_load(file)

        return cls.model_validate(config)

    @classmethod
    def from_string(cls, raw: str) -> "Flow":
        data = yaml.safe_load(raw)

        # return msgspec.yaml.decode(raw, type=cls)

        _logger.warning(f"Data: {data}")

        jobs = []
        for job_data in data.get("jobs", []):
            actions = [
                Action(**action_data) for action_data in job_data.get("actions", [])
            ]

            # actions = [
            #     msgspec.json.decode(json.dumps(action_data), type=Action)
            #     for action_data in job_data.get("actions", [])
            # ]
            job = Job(name=job_data["name"], steps=actions)
            jobs.append(job)

        # Step 3: Create the Flow object and initialize its groups
        flow = cls(jobs=jobs)
        return flow

        # return cls.model_validate(config)


if __name__ == "__main__":
    data = """
jobs:
  - name: job1
    truc: xxx
    steps:
      - name: examplex
        wait: true
        autre: false
      - name: example
        wait: false
      - name: example
        wait: true
  - name: job2
    steps:
      - name: example
        wait: false
      - name: example
        wait: true
"""
    # from kinetik import load_all_actions

    print(settings.logfile)

    # load_all_actions()
    print("actions: " % Action.list())
    flow = Flow.from_string(data)
    flow.execute()
