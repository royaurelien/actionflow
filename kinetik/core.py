import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Generator

import yaml

from kinetik.actions.base import Action
from kinetik.exceptions import ActionNotFound
from kinetik.flow import FlowSchema
from kinetik.jobs import JobSchema, JobsSchema
from kinetik.logger import _logger
from kinetik.tools import SingletonMeta, load_yaml_with_context


@dataclass(frozen=False)
class Client(metaclass=SingletonMeta):
    context: FlowSchema
    jobs: JobsSchema

    def __post_init__(self):
        self.stop_event = threading.Event()

    def next_job(self) -> Generator[JobSchema, None, None]:
        """
        Get the next job to run.
        """
        for job in self.jobs.jobs:
            yield job.name, job

    def _run_action_in_thread(self, action):
        """
        Run an action in a separate thread and return the result.
        """
        if self.stop_event.is_set():
            _logger.warning(f"Action {action.name} aborted due to stop signal.")
            return False

        try:
            _logger.info(f"Executing action: {action.name}")
            action.set_context(self.context)
            result = action.run(ctx=self.context)
            return result
        except Exception as e:
            _logger.error(f"Action {action.name} failed: {e}")
            self.stop_event.set()  # Signal all threads to stop
            raise

    def run_in_threads(self, job: JobSchema) -> Generator[tuple, None, None]:
        """
        Execute each group of actions sequentially, actions within a group concurrently.
        """

        # job = self.jobs.by_name(job_name)

        with ThreadPoolExecutor() as executor:
            # Iterate over groups of actions
            for group_index, group in enumerate(job.grouped):
                _logger.info(
                    f"Running group {group_index + 1}/{len(job.grouped)}: {", ".join(list(map(lambda x: x.name, group)))}"
                )

                # Start each action in the group concurrently
                futures = {
                    executor.submit(self._run_action_in_thread, action): action
                    for action in group
                }

                # Wait for all futures (threads) to complete and gather results
                for future in as_completed(futures):
                    action = futures[future]
                    try:
                        result = future.result()  # Capture result from the thread
                        _logger.info(
                            f"Action {action._id} finished with result: {result}"
                        )
                        yield (action._id, result)

                    except Exception as e:
                        _logger.error(f"Error executing action {action._id}: {e}")
                        return (action.name, False)

    @staticmethod
    def load_actions(raw: str, context: dict = {}) -> Generator[dict, None, None]:
        """
        Load actions from a YAML file with environment and context.
        """

        def _load_actions(vals: dict) -> JobSchema:
            actions = []
            for item in vals["steps"]:
                params = item.get("with", {})
                try:
                    action = Action.by_name(item["name"], **params)
                    actions.append(action)
                except ActionNotFound as error:
                    _logger.error("Error loading action: %s", error)
                    sys.exit(1)
            return JobSchema(name=vals["name"], steps=actions)

        data = load_yaml_with_context(raw, context)
        for vals in data["upgrade"]["jobs"]:
            yield _load_actions(vals)

    @classmethod
    def from_file(cls, filepath: str) -> "Client":
        """
        Load an upgrade file and return an Upgrade instance.
        """

        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = f.read()
            raw_yaml = yaml.safe_load(raw_data)
            context = FlowSchema(
                **{k: v for k, v in raw_yaml["upgrade"].items() if k != "jobs"}
            )

            jobs = []
            for job in cls.load_actions(raw_data, context.env):
                jobs.append(job)

        return cls(context=context, jobs=JobsSchema(jobs=jobs))
