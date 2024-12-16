import os
import re
import subprocess
import sys
from datetime import datetime
from functools import wraps
from string import Template
from typing import Any, List

import yaml

try:
    from git import InvalidGitRepositoryError, Repo
except ImportError:
    Repo = None


from actionflow.logger import _logger
from actionflow.settings import Environment

PID_FILE = "/tmp/actionflow.pid"


# def effective_access(*args, **kwargs):
#     if "effective_ids" not in kwargs:
#         try:
#             kwargs["effective_ids"] = os.access in os.supports_effective_ids
#         except AttributeError:
#             pass

#     return os.access(*args, **kwargs)


# def determine_pid_directory():
#     uid = os.geteuid() if hasattr(os, "geteuid") else os.getuid()

#     paths = [
#         "/run/user/%s/" % uid,
#         "/var/run/user/%s/" % uid,
#         "/run/",
#         "/var/run/",
#     ]

#     for path in paths:
#         if effective_access(os.path.realpath(path), os.W_OK | os.X_OK):
#             return path

#     return tempfile.gettempdir()


# PID_DIR = determine_pid_directory()


def create_pidfile() -> None:
    if os.path.exists(PID_FILE):
        print(f"The programme is already running : {PID_FILE}")
        sys.exit(1)
    with open(PID_FILE, "w") as lock_file:
        lock_file.write(str(os.getpid()))


def remove_pidfile() -> None:
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def group_by(items: List[Any], key: str):
    """
    Groups a list of items based on the boolean value of a specified attribute.

    Args:
        items (List[Any]): The list of items to be grouped.
        key (str): The attribute name used to determine the grouping.

    Returns:
        List[List[Any]]: A list of groups, where each group is a list of items
        that share the same boolean value for the specified attribute.

    Example:
        class Item:
            def __init__(self, flag):
                self.flag = flag

        items = [Item(True), Item(True), Item(False), Item(False), Item(True)]
        grouped = group_by(items, 'flag')
        # grouped will be [[Item(True), Item(True)], [Item(False), Item(False)], [Item(True)]]
    """
    result = []
    current_group = []
    for item in items:
        if getattr(item, key) is True:
            if current_group:
                if getattr(current_group[-1], key) is True:
                    current_group.append(item)
                else:
                    result.append(current_group)
                    current_group = [item]
            else:
                current_group = [item]
        elif getattr(item, key) is False:
            if current_group:
                if getattr(current_group[-1], key) is True:
                    current_group.append(item)
                    result.append(current_group)
                    current_group = []
                else:
                    result.append(current_group)
                    current_group = [item]
            else:
                current_group = [item]

    if current_group:
        result.append(current_group)

    return result


def update(fieldnames: str):
    def decorator_repeat(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            self = args[0]

            obj = self
            attrs = fieldnames.split(".")
            for attr in attrs[:-1]:
                obj = getattr(obj, attr)
            setattr(obj, attrs[-1], datetime.now())

            return value

        return wrapper

    return decorator_repeat


def parse_yaml(raw: str, context: dict = {}) -> dict:
    """
    Parses a YAML string with optional context for variable substitution.

    Args:
        raw (str): The raw YAML string to be parsed.
        context (dict, optional): A dictionary of variables to substitute into the YAML string. Defaults to an empty dictionary.

    Returns:
        dict: The parsed YAML content as a dictionary.
    """
    template = Template(raw)
    env = Environment()

    substituted_yaml = template.safe_substitute({**context, **env.model_dump()})
    return yaml.safe_load(substituted_yaml)


def sync_directories(source: str, target: str) -> bool:
    """
    Synchronize contents of source directory to target directory using rsync.

    :param source: Path to the source directory.
    :param target: Path to the target directory.
    """

    if not source.endswith("/"):
        source += "/"

    if not target.endswith("/"):
        target += "/"

    command = ["rsync", "-av", source, target]
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    if result.returncode == 0:
        _logger.info(f"Synced {source} to {target} successfully.")
        _logger.debug(result.stdout)
        return True

    _logger.error(f"Error syncing {source} to {target}:")
    _logger.error(result.stderr)
    return False


def get_directory_size(path: str) -> int:
    """
    Calculate the total size of all files in a given directory.

    Args:
        path (str): The path to the directory.

    Returns:
        int: The total size of all files in the directory in bytes.
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
    return total_size


def run_command(command: list[str]) -> bool:
    """
    Executes a command in a subprocess and returns whether it was successful.

    Args:
        command (list[str]): The command to run as a list of strings.

    Returns:
        bool: True if the command executed successfully (return code 0), False otherwise.
    """
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0


def render_template(raw: str, **kwargs) -> str:
    """
    Renders a template string with the provided keyword arguments.

    Args:
        raw (str): The raw template string to be rendered.
        **kwargs: Arbitrary keyword arguments to be substituted in the template.

    Returns:
        str: The rendered template string with the substitutions made.
    """
    template = Template(raw)
    return template.safe_substitute(kwargs)


def clean_url(url: str) -> str:
    """
    Removes credentials from a URL if present and replaces http with https.
    """

    # Regex to match URLs with credentials
    pattern = re.compile(r"(https?://|http://)([^@]+@)?(.+)")

    # Substitute the matched pattern to remove credentials and ensure https
    cleaned_url = pattern.sub(lambda m: f"https://{m.group(3)}", url)  # noqa: E231

    return cleaned_url


def parse_repository_url(url: str) -> List[str]:
    """
    Parses a repository URL to extract the cleaned URL, owner and repository name.
    Args:
        url (str): The URL of the repository.
    Returns:
        List[str]: A list containing the cleaned URL, owner and repository name.
    """

    parts = url.split("/")
    owner = parts[-2]
    repo = parts[-1].replace(".git", "")

    url = clean_url(url)

    return url, owner, repo


def get_local_repository(path: str, remote_name: str = "origin") -> tuple:
    try:
        repo = Repo(path)
        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = "detached HEAD"

        remote = (
            next(repo.remote(remote_name).urls, None)
            if remote_name in repo.remotes
            else None
        )

    except InvalidGitRepositoryError as error:
        _logger.info(f"Invalid Git repository: {error}")
        return None, None

    return branch, remote
