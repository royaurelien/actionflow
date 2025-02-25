import os
from pathlib import Path

from pydantic_settings import BaseSettings


def get_default_path():
    return str(Path.home() / ".actionflow")


class Environment(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"
        env_prefix = "AF_"


class Settings(BaseSettings):
    _name: str = "actionflow"
    _path: str = str(Path.home() / ".actionflow")
    _logname: str = "main.log"

    debug: bool = False
    env: Environment = Environment()

    @property
    def state_filepath(self):
        return os.path.join(self._path, "state.json")

    @property
    def logfile(self):
        return os.path.join(self._path, self._logname)

    def get_path(self, *args):
        return os.path.join(self._path, *args)

    def setup_workdir(self):
        print("Setting up workdir {}".format(self._path))
        print(self.logfile)
        path = Path(self._path)
        path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.setup_workdir()
