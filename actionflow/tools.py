import os
import sys
from datetime import datetime
from functools import wraps
from string import Template
from typing import Any, List

import yaml

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
        if getattr(item, key) is False:
            if current_group:
                if getattr(current_group[-1], key) is False:
                    current_group.append(item)
                else:
                    result.append(current_group)
                    current_group = [item]
            else:
                current_group = [item]
        elif getattr(item, key) is True:
            if current_group:
                if getattr(current_group[-1], key) is False:
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
