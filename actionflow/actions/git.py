from actionflow.action import Action
from actionflow.logger import _logger
from actionflow.tools import Repo, get_local_repository, parse_repository_url


class Checkout(Action):
    name: str = "checkout"
    description: str = "Checkout Git repository"

    repository: str
    branch: str
    path: str
    token: str = None
    skip: bool = True

    def _check(self) -> bool:
        _logger.info("Checking repository status")
        branch, remote = get_local_repository(self.path)

        _logger.info(f"Current branch: {branch}")
        _logger.info(f"Current remote: {remote}")

        if branch != self.branch:
            _logger.info(f"Current branch is {branch}, expected {self.branch}")
            return False

        if self.repository not in remote:
            _logger.info(f"Current remote is {remote}, expected {self.repository}")
            return False

        return True

    def _run(self) -> bool:
        if self._check():
            _logger.info("Repository is already checked out")
            return True

        url, _, repo = parse_repository_url(self.repository)

        _logger.info("Cloning %s repository to %s", repo, self.path)

        repo = Repo.clone_from(url, self.path)
        repo.git.checkout(self.branch)
        repo.git.execute(
            command=["git", "submodule", "update", "--init", "--recursive"]
        )

        return True
