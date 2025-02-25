import logging
import os

from actionflow.action import Action
from actionflow.tools import Repo, get_local_repository, parse_repository_url


class Checkout(Action):
    name: str = "checkout"
    description: str = "Checkout Git repository"
    skip: bool = True

    repository: str
    branch: str
    path: str
    token: str = None
    skip: bool = True

    def _check(self) -> bool:
        logging.debug("Checking repository status")
        try:
            branch, remote = get_local_repository(self.path)
        except Exception as e:
            logging.error(f"Error checking repository: {e}")
            return False

        logging.debug(f"Current branch: {branch}")
        logging.debug(f"Current remote: {remote}")

        if branch != self.branch:
            logging.warning(f"Current branch is {branch}, expected {self.branch}")
            return False

        if self.repository not in remote:
            logging.warning(f"Current remote is {remote}, expected {self.repository}")
            return False

        return True

    def _pre_process(self):
        logging.debug(f"Checking out {self.repository} to {self.path}")
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def _run(self) -> bool:
        if self._check():
            logging.debug("Repository is already checked out")
            return True

        url, _, repo = parse_repository_url(self.repository)

        logging.info("Cloning %s repository to %s", repo, self.path)

        repo = Repo.clone_from(url, self.path, single_branch=True, b=self.branch)
        repo.git.execute(
            command=["git", "submodule", "update", "--init", "--recursive"]
        )

        return True
