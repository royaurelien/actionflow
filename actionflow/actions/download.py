import logging
import os

from actionflow.action import Action
from actionflow.net import download_file


class Download(Action):
    name: str = "download"
    description: str = "Download a file from a URL"
    skip: bool = True
    url: str
    timeout: int = 60
    filepath: str

    def _pre_process(self) -> None:
        if os.path.exists(self.filepath):
            logging.warning("File already exists: %s", self.filepath)
            os.remove(self.filepath)

    def _run(self) -> bool:
        logging.info(
            "Downloading from %s with timeout %d",
            self.url,
            self.timeout,
        )
        download_file(self.url, self.filepath, timeout=self.timeout)
        return True

    def _check(self) -> bool:
        return os.path.exists(self.filepath)
