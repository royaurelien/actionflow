import os
from pathlib import Path

from pydantic_settings import BaseSettings

__all__ = ["settings"]


def get_default_workdir():
    return str(Path.home() / ".upgrades")


class Environment(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"
        # env_prefix = "UPG_"


class Settings(BaseSettings):
    workdir: str = os.getenv("KINETIK_WORKDIR", default=get_default_workdir())
    logfile: str = "main.log"

    env: Environment = Environment()

    @property
    def config_dir(self):
        return os.path.join(self.workdir, ".config")

    @property
    def state_file(self):
        return os.path.join(self.workdir, ".config", "state.json")

    def get_path(self, *args):
        return os.path.join(self.workdir, *args)

    def setup_workdir(self):
        workdir = Path(self.workdir)
        workdir.mkdir(parents=True, exist_ok=True)

        (workdir / ".config").mkdir(parents=True, exist_ok=True)
        (workdir / "logs").mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.setup_workdir()
