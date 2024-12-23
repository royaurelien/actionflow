import logging
import os

from actionflow.action import Action
from actionflow.tools import get_directory_size, run_command, sync_directories


class SyncDirectories(Action):
    """
    Sync directories using rsync
    """

    name: str = "sync-directories"
    description: str = "Sync directories using rsync"

    source: str
    target: str

    def _pre_process(self):
        """
        Check if the source and target filestores exist
        """
        paths = [self.source, self.target]
        for path in paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Source filestore not found: {path}")

    def _run(self):
        """
        Sync the source filestore to the target filestore with rsync
        """
        return sync_directories(self.source, self.target)

    def _check(self):
        """
        Check if the target filestore is larger or equal to the source filestore
        """
        return get_directory_size(self.target) >= get_directory_size(self.source)


class FixRights(Action):
    """
    Fix the rights of the data directory
    """

    name: str = "fix-rights"
    description: str = "Fix data directory rights"
    mode: str
    path: str

    def _run(self):
        try:
            return run_command(["sudo", "chown", "-R", self.mode, self.path])

        except Exception as e:
            logging.error(f"Failed to fix rights: {e}")
            return False
