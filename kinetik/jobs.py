from typing import Dict, List

from pydantic import BaseModel

from kinetik.actions.base import Action
from kinetik.tools import group_by


class JobSchema(BaseModel):
    name: str
    steps: List[Action]

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


class JobsSchema(BaseModel):
    jobs: List[JobSchema]
    _jobs: Dict[str, JobSchema]

    @property
    def length(self) -> int:
        return sum(
            map(
                lambda item: item.length,
                self.jobs,
            )
        )

    def model_post_init(self, __context):
        self._jobs = {job.name: job for job in self.jobs}
        for index, job in enumerate(self.jobs, start=1):
            job.set_indexes(index)
        return super().model_post_init(__context)

    def by_name(self, name: str) -> JobSchema:
        return self._jobs.get(name)
